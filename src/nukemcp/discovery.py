"""Nuke installation discovery and headless launcher."""

from __future__ import annotations

import base64
import json
import logging
import os
import platform
import re
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger(__name__)

_VERSION_RE = re.compile(r"Nuke(\d+)\.(\d+)(v\d+)?")


@dataclass
class NukeInstall:
    executable: Path
    version: str
    major: int
    minor: int
    patch: str
    source: str

    def __str__(self) -> str:
        return f"Nuke {self.version} at {self.executable} (via {self.source})"


@dataclass
class LicenseInfo:
    found: bool = False
    license_type: str = ""  # "env_var", "rlm_server", "license_file", "trial", "none"
    detail: str = ""
    features: list[str] = field(default_factory=list)
    expires: datetime | None = None

    def __str__(self) -> str:
        if not self.found:
            return f"No Nuke license found. {self.detail}"
        parts = [f"License ({self.license_type}): {self.detail}"]
        if self.features:
            parts.append(f"Features: {', '.join(self.features)}")
        if self.expires:
            remaining = self.expires - datetime.now(timezone.utc)
            if remaining.total_seconds() > 0:
                parts.append(f"Expires: {self.expires:%Y-%m-%d} ({remaining.days} days remaining)")
            else:
                parts.append(f"EXPIRED: {self.expires:%Y-%m-%d}")
        return " | ".join(parts)


@dataclass
class DiscoveryResult:
    installations: list[NukeInstall] = field(default_factory=list)
    license: LicenseInfo = field(default_factory=LicenseInfo)
    breadcrumbs: dict[str, str] = field(default_factory=dict)

    @property
    def has_nuke(self) -> bool:
        return len(self.installations) > 0

    @property
    def best(self) -> NukeInstall | None:
        if not self.installations:
            return None
        return sorted(
            self.installations,
            key=lambda i: (i.major, i.minor, i.patch),
            reverse=True,
        )[0]

    def summary(self) -> str:
        lines = []
        if self.installations:
            lines.append(f"Found {len(self.installations)} Nuke installation(s):")
            for inst in self.installations:
                lines.append(f"  {inst}")
        else:
            lines.append("No Nuke installations found.")
            if self.breadcrumbs:
                lines.append("Breadcrumbs suggest Nuke has been run on this machine:")
                for key, val in self.breadcrumbs.items():
                    lines.append(f"  {key}: {val}")
                lines.append(
                    "The executable may be on an unmounted drive "
                    "or in a non-standard location."
                )
        lines.append(str(self.license))
        return "\n".join(lines)


# -- Version parsing ----------------------------------------------------------

def _parse_nuke_path(path: Path) -> tuple[str, int, int, str] | None:
    for name in [path.name, path.parent.name]:
        m = _VERSION_RE.search(name)
        if m:
            major, minor = int(m.group(1)), int(m.group(2))
            patch = m.group(3) or ""
            return f"{major}.{minor}{patch}", major, minor, patch
    return None


def _make_install(path: Path, source: str) -> NukeInstall | None:
    parsed = _parse_nuke_path(path)
    if not parsed:
        return None
    version, major, minor, patch = parsed
    return NukeInstall(path, version, major, minor, patch, source)


# -- Search strategies --------------------------------------------------------

def _find_executables_in_dir(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return [
        e for e in directory.iterdir()
        if _VERSION_RE.match(e.name) and e.is_file() and os.access(e, os.X_OK)
    ]


def _search_standard_paths() -> list[NukeInstall]:
    system = platform.system()
    search_dirs: list[Path] = []

    if system == "Linux":
        search_dirs.extend(Path("/usr/local").glob("Nuke*"))
        search_dirs.extend(Path("/opt").glob("Nuke*"))
    elif system == "Darwin":
        search_dirs.extend(Path("/Applications").glob("Nuke*"))
    elif system == "Windows":
        prog = Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        search_dirs.extend(prog.glob("Nuke*"))

    installs = []
    for d in search_dirs:
        for exe in _find_executables_in_dir(d):
            inst = _make_install(exe, "standard_path")
            if inst:
                installs.append(inst)
    return installs


def _search_desktop_files() -> list[NukeInstall]:
    if platform.system() != "Linux":
        return []

    installs = []
    for d in [Path("/usr/share/applications"), Path.home() / ".local/share/applications"]:
        if not d.is_dir():
            continue
        for df in d.glob("*uke*.desktop"):
            text = df.read_text()
            for line in text.splitlines():
                if line.startswith("Exec="):
                    exe_path = line.split("=", 1)[1].split()[0].strip('"')
                    p = Path(exe_path)
                    if p.is_file() and os.access(p, os.X_OK):
                        inst = _make_install(p, "desktop_file")
                        if inst:
                            installs.append(inst)
    return installs


def _search_running_processes() -> list[NukeInstall]:
    if platform.system() != "Linux":
        return []

    installs = []
    for pid_dir in Path("/proc").iterdir():
        if not pid_dir.name.isdigit():
            continue
        try:
            target = (pid_dir / "exe").resolve(strict=True)
            if _VERSION_RE.search(target.name):
                inst = _make_install(target, "running_process")
                if inst:
                    installs.append(inst)
        except (OSError, PermissionError):
            continue
    return installs


def _search_mounted_volumes() -> list[NukeInstall]:
    system = platform.system()
    mount_roots: list[Path] = []

    if system == "Linux":
        for parent in [Path("/media"), Path("/mnt")]:
            if not parent.is_dir():
                continue
            try:
                children = list(parent.iterdir())
            except PermissionError:
                continue
            for child in children:
                if not child.is_dir():
                    continue
                if parent.name == "media":
                    try:
                        mount_roots.extend(
                            v for v in child.iterdir() if v.is_dir()
                        )
                    except PermissionError:
                        continue
                else:
                    mount_roots.append(child)
    elif system == "Darwin":
        volumes = Path("/Volumes")
        if volumes.is_dir():
            mount_roots.extend(v for v in volumes.iterdir() if v.is_dir())

    installs = []
    for root in mount_roots:
        for pattern in ["Nuke*", "*/Nuke*", "*/*/Nuke*", "*/*/*/Nuke*"]:
            for nuke_dir in root.glob(pattern):
                if not nuke_dir.is_dir():
                    continue
                for exe in _find_executables_in_dir(nuke_dir):
                    inst = _make_install(exe, "mounted_volume")
                    if inst:
                        installs.append(inst)
    return installs


def _search_env_var() -> list[NukeInstall]:
    nuke_exe = os.environ.get("NUKE_EXE")
    if not nuke_exe:
        return []
    p = Path(nuke_exe)
    if p.is_file() and os.access(p, os.X_OK):
        inst = _make_install(p, "NUKE_EXE")
        if inst:
            return [inst]
    return []


# -- Breadcrumbs --------------------------------------------------------------

def _detect_breadcrumbs() -> dict[str, str]:
    crumbs: dict[str, str] = {}
    home = Path.home()

    if (home / ".nuke").is_dir():
        crumbs["dot_nuke"] = "~/.nuke/ exists"

    docs_nuke = home / "Documents" / "nuke"
    if docs_nuke.is_dir():
        for child in docs_nuke.iterdir():
            m = re.match(r"(\d+\.\d+)\.\d+", child.name)
            if m:
                crumbs["cache"] = f"Nuke {m.group(1)} cache at {child}"

    uid = getattr(os, "getuid", lambda: None)()
    if uid is not None:
        tmp = Path(f"/var/tmp/nuke-u{uid}")
        if tmp.is_dir():
            crumbs["tmp"] = f"Nuke temp dir at {tmp}"

    nv_cache = home / ".nv" / "NukeComputeCache"
    if nv_cache.is_dir():
        crumbs["gpu_cache"] = f"GPU compute cache at {nv_cache}"

    return crumbs


# -- License detection --------------------------------------------------------

def _foundry_tokens_dir() -> Path | None:
    system = platform.system()
    if system == "Linux":
        d = Path.home() / ".local" / "share" / "Foundry" / "Tokens"
    elif system == "Darwin":
        d = Path.home() / "Library" / "Application Support" / "Foundry" / "Tokens"
    elif system == "Windows":
        d = Path(os.environ.get("LOCALAPPDATA", "")) / "Foundry" / "Tokens"
    else:
        return None
    return d if d.is_dir() else None


def _parse_jwt_payload(token_text: str) -> dict | None:
    parts = token_text.strip().split(".")
    if len(parts) < 2:
        return None
    payload = parts[1] + "=" * (4 - len(parts[1]) % 4)
    return json.loads(base64.urlsafe_b64decode(payload))


def _detect_trial_tokens() -> LicenseInfo | None:
    tokens_dir = _foundry_tokens_dir()
    if not tokens_dir:
        return None

    jwt_files = list(tokens_dir.glob("*.jwt"))
    if not jwt_files:
        return None

    features: list[str] = []
    latest_expiry: datetime | None = None

    for jf in jwt_files:
        payload = _parse_jwt_payload(jf.read_text())
        if not payload:
            continue
        feature = payload.get("feature", "")
        if feature:
            features.append(feature)
        exp = payload.get("exp")
        if exp:
            expiry = datetime.fromtimestamp(exp, tz=timezone.utc)
            if latest_expiry is None or expiry > latest_expiry:
                latest_expiry = expiry

    if not features:
        return None

    return LicenseInfo(
        found=True,
        license_type="trial",
        detail=f"Foundry trial tokens in {tokens_dir}",
        features=features,
        expires=latest_expiry,
    )


def detect_license() -> LicenseInfo:
    for var in ["FOUNDRY_LICENSE_FILE", "foundry_LICENSE"]:
        val = os.environ.get(var, "")
        if val:
            if "@" in val:
                return LicenseInfo(True, "rlm_server", f"{var}={val}")
            if Path(val).is_file():
                return LicenseInfo(True, "license_file", f"{var}={val}")
            return LicenseInfo(False, "env_var_invalid", f"{var}='{val}' but target not found")

    for lp in [
        Path.home() / ".foundry" / "foundry.lic",
        Path("/usr/local/foundry/RLM/foundry.lic"),
        Path("/opt/foundry/RLM/foundry.lic"),
        Path.home() / ".nuke" / "foundry.lic",
    ]:
        if lp.is_file():
            return LicenseInfo(True, "license_file", str(lp))

    trial = _detect_trial_tokens()
    if trial:
        return trial

    return LicenseInfo(
        False, "none",
        "Checked FOUNDRY_LICENSE_FILE, standard license paths, "
        "and Foundry trial tokens. "
        "Set FOUNDRY_LICENSE_FILE=port@host or install a license via "
        "https://www.foundry.com/trial",
    )


# -- Main discovery -----------------------------------------------------------

def discover_nuke(extra_paths: list[str] | None = None) -> DiscoveryResult:
    result = DiscoveryResult()
    result.breadcrumbs = _detect_breadcrumbs()
    result.license = detect_license()

    seen: set[Path] = set()

    for name, fn in [
        ("env_var", _search_env_var),
        ("standard_paths", _search_standard_paths),
        ("desktop_files", _search_desktop_files),
        ("running_processes", _search_running_processes),
        ("mounted_volumes", _search_mounted_volumes),
    ]:
        try:
            for inst in fn():
                resolved = inst.executable.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    result.installations.append(inst)
        except Exception as e:
            log.debug("Search strategy %s failed: %s", name, e)

    if extra_paths:
        for ep in extra_paths:
            p = Path(ep)
            if p.is_file() and os.access(p, os.X_OK):
                inst = _make_install(p, "user_specified")
                if inst and p.resolve() not in seen:
                    seen.add(p.resolve())
                    result.installations.append(inst)
            elif p.is_dir():
                for exe in _find_executables_in_dir(p):
                    inst = _make_install(exe, "user_specified")
                    if inst and exe.resolve() not in seen:
                        seen.add(exe.resolve())
                        result.installations.append(inst)

    return result


# -- Headless launcher --------------------------------------------------------

_BOOTSTRAP = """\
import sys, os
sys.path.insert(0, os.path.dirname({addon_path!r}))
import nuke_mcp_addon
server = nuke_mcp_addon.NukeMCPServer(port={port})
print("NukeMCP addon listening on port {port}", file=sys.stderr)
server.serve_forever()
"""


def launch_headless(
    executable: Path | str,
    port: int = 54321,
    addon_path: str | None = None,
    timeout: float = 30.0,
) -> subprocess.Popen:
    executable = Path(executable)
    if not executable.is_file():
        raise FileNotFoundError(f"Nuke executable not found: {executable}")

    if addon_path is None:
        addon_path = _find_addon()
    if not addon_path or not Path(addon_path).is_file():
        raise FileNotFoundError(
            "nuke_mcp_addon.py not found. "
            "Copy nuke_addon/nuke_mcp_addon.py to ~/.nuke/ or pass addon_path."
        )

    bootstrap = tempfile.NamedTemporaryFile(
        mode="w", suffix="_nukemcp_bootstrap.py", delete=False
    )
    bootstrap.write(_BOOTSTRAP.format(addon_path=addon_path, port=port))
    bootstrap.close()

    cmd = [str(executable), "-t", "-i", bootstrap.name]
    log.info("Launching headless Nuke: %s", " ".join(cmd))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    start = time.monotonic()
    while time.monotonic() - start < timeout:
        if proc.poll() is not None:
            _, stderr = proc.communicate(timeout=5)
            _cleanup(bootstrap.name)
            raise RuntimeError(
                f"Nuke exited with code {proc.returncode}.\n"
                f"stderr: {stderr.decode('utf-8', errors='replace')}"
            )
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0):
                log.info("Headless Nuke ready on port %d (PID %d)", port, proc.pid)
                _cleanup(bootstrap.name)
                return proc
        except (ConnectionRefusedError, OSError, TimeoutError):
            time.sleep(0.5)

    proc.terminate()
    proc.wait(timeout=5)
    _cleanup(bootstrap.name)
    raise RuntimeError(
        f"Timed out after {timeout}s waiting for Nuke addon on port {port}."
    )


def stop_headless(proc: subprocess.Popen, timeout: float = 10.0) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _find_addon() -> str | None:
    for c in [
        Path.home() / ".nuke" / "nuke_mcp_addon.py",
        Path(__file__).parent.parent.parent / "nuke_addon" / "nuke_mcp_addon.py",
    ]:
        if c.is_file():
            return str(c.resolve())
    return None


def _cleanup(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass
