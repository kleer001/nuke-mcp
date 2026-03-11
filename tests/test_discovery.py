"""Tests for Nuke discovery and headless launcher."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from nukemcp.discovery import (
    DiscoveryResult,
    LicenseInfo,
    NukeInstall,
    _detect_breadcrumbs,
    _detect_trial_tokens,
    _make_install,
    _parse_jwt_payload,
    _parse_nuke_path,
    detect_license,
    discover_nuke,
)


def test_parse_nuke_path_executable():
    parsed = _parse_nuke_path(Path("/usr/local/Nuke17.0v1/Nuke17.0"))
    assert parsed == ("17.0", 17, 0, "")


def test_parse_nuke_path_with_patch():
    parsed = _parse_nuke_path(Path("/usr/local/Nuke17.0v1/Nuke17.0v1"))
    assert parsed is not None
    version, major, minor, patch = parsed
    assert major == 17
    assert minor == 0
    assert patch == "v1"


def test_parse_nuke_path_from_parent():
    parsed = _parse_nuke_path(Path("/opt/Nuke16.1v2/some_binary"))
    assert parsed is not None
    version, major, minor, patch = parsed
    assert major == 16
    assert minor == 1
    assert patch == "v2"


def test_parse_nuke_path_no_match():
    assert _parse_nuke_path(Path("/usr/bin/python3")) is None


def test_make_install():
    inst = _make_install(Path("/usr/local/Nuke17.0v1/Nuke17.0"), "test")
    assert inst is not None
    assert inst.major == 17
    assert inst.minor == 0
    assert inst.source == "test"


def test_make_install_no_match():
    assert _make_install(Path("/usr/bin/python3"), "test") is None


def test_discovery_result_best():
    r = DiscoveryResult()
    r.installations = [
        NukeInstall(Path("/a/Nuke16.0"), "16.0", 16, 0, "", "test"),
        NukeInstall(Path("/b/Nuke17.0"), "17.0", 17, 0, "", "test"),
    ]
    assert r.best.major == 17


def test_discovery_result_empty():
    r = DiscoveryResult()
    assert not r.has_nuke
    assert r.best is None


def test_license_none():
    with patch.dict("os.environ", {}, clear=True):
        with patch("nukemcp.discovery._foundry_tokens_dir", return_value=None):
            info = detect_license()
            assert not info.found
            assert info.license_type == "none"


def test_license_env_var_server():
    with patch.dict("os.environ", {"FOUNDRY_LICENSE_FILE": "4101@license-server"}):
        info = detect_license()
        assert info.found
        assert info.license_type == "rlm_server"


def test_license_env_var_file(tmp_path):
    lic_file = tmp_path / "foundry.lic"
    lic_file.write_text("LICENSE foundry")
    with patch.dict("os.environ", {"FOUNDRY_LICENSE_FILE": str(lic_file)}):
        info = detect_license()
        assert info.found
        assert info.license_type == "license_file"


def test_license_env_var_missing_file():
    with patch.dict("os.environ", {"FOUNDRY_LICENSE_FILE": "/nonexistent/foundry.lic"}):
        info = detect_license()
        assert not info.found
        assert info.license_type == "env_var_invalid"


def test_discover_with_extra_path(tmp_path):
    exe = tmp_path / "Nuke17.0v1" / "Nuke17.0"
    exe.parent.mkdir()
    exe.touch()
    exe.chmod(0o755)

    result = discover_nuke(extra_paths=[str(exe.parent)])
    assert result.has_nuke
    assert result.best.major == 17


def test_summary_no_installations():
    r = DiscoveryResult()
    r.license = LicenseInfo(False, "none", "no license")
    r.breadcrumbs = {"dot_nuke": "~/.nuke/ exists"}
    s = r.summary()
    assert "No Nuke installations found" in s
    assert "Breadcrumbs" in s
    assert "no license" in s


def _make_fake_jwt(payload: dict) -> str:
    """Build a minimal unsigned JWT for testing."""
    import base64, json
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.fakesig"


def test_parse_jwt_payload():
    token = _make_fake_jwt({"feature": "nuke_i", "exp": 1775842157})
    payload = _parse_jwt_payload(token)
    assert payload["feature"] == "nuke_i"
    assert payload["exp"] == 1775842157


def test_parse_jwt_payload_invalid():
    assert _parse_jwt_payload("not-a-jwt") is None


def test_detect_trial_tokens(tmp_path):
    tokens_dir = tmp_path / "Foundry" / "Tokens"
    tokens_dir.mkdir(parents=True)

    exp_ts = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
    (tokens_dir / "nuke_i_test.jwt").write_text(
        _make_fake_jwt({"feature": "nuke_i", "exp": exp_ts})
    )
    (tokens_dir / "nukex_i_test.jwt").write_text(
        _make_fake_jwt({"feature": "nukex_i", "exp": exp_ts})
    )

    with patch("nukemcp.discovery._foundry_tokens_dir", return_value=tokens_dir):
        info = _detect_trial_tokens()
    assert info is not None
    assert info.found
    assert info.license_type == "trial"
    assert "nuke_i" in info.features
    assert "nukex_i" in info.features
    assert info.expires == datetime.fromtimestamp(exp_ts, tz=timezone.utc)


def test_detect_trial_tokens_empty(tmp_path):
    tokens_dir = tmp_path / "Foundry" / "Tokens"
    tokens_dir.mkdir(parents=True)

    with patch("nukemcp.discovery._foundry_tokens_dir", return_value=tokens_dir):
        assert _detect_trial_tokens() is None


def test_detect_license_finds_trial(tmp_path):
    tokens_dir = tmp_path / "Foundry" / "Tokens"
    tokens_dir.mkdir(parents=True)
    exp_ts = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp())
    (tokens_dir / "nuke_i_test.jwt").write_text(
        _make_fake_jwt({"feature": "nuke_i", "exp": exp_ts})
    )

    with patch.dict("os.environ", {}, clear=True):
        with patch("nukemcp.discovery._foundry_tokens_dir", return_value=tokens_dir):
            info = detect_license()
    assert info.found
    assert info.license_type == "trial"


def test_license_info_str_with_expiry():
    info = LicenseInfo(
        found=True,
        license_type="trial",
        detail="tokens found",
        features=["nuke_i", "nukex_i"],
        expires=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    s = str(info)
    assert "trial" in s
    assert "nuke_i" in s
    assert "2026-06-01" in s
