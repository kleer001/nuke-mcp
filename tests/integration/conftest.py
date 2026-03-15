"""Integration test fixtures — connect to a real headless Nuke instance.

Run with: uv run pytest -m integration
Requires a Nuke installation and valid license.
"""

import os
import subprocess
import time

import pytest

from nukemcp.connection import NukeConnection

NUKE_PORT = int(os.environ.get("NUKEMCP_TEST_PORT", "54322"))
NUKE_EXE = os.environ.get("NUKE_EXE", "")


def _find_nuke() -> str | None:
    """Try to find a Nuke executable."""
    if NUKE_EXE:
        return NUKE_EXE
    try:
        from nukemcp.discovery import discover_nuke

        result = discover_nuke()
        if result.has_nuke:
            return str(result.best.executable)
    except Exception:
        pass
    return None


@pytest.fixture(scope="session")
def nuke_process():
    """Launch headless Nuke for the test session."""
    exe = _find_nuke()
    if not exe:
        pytest.skip("No Nuke executable found (set NUKE_EXE or install Nuke)")

    addon_path = os.path.join(os.path.dirname(__file__), "..", "..", "nuke_addon")

    proc = subprocess.Popen(
        [
            exe, "-t", "-i", "--",
            "-c", (
                f"import sys; sys.path.insert(0, {addon_path!r}); "
                f"import nuke_mcp_addon; "
                f"s = nuke_mcp_addon.NukeMCPServer(port={NUKE_PORT}); "
                f"s.serve_forever()"
            ),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to start
    for _ in range(30):
        try:
            conn = NukeConnection("127.0.0.1", NUKE_PORT)
            conn.connect(retries=1, base_delay=0.1)
            conn.disconnect()
            break
        except Exception:
            time.sleep(1)
    else:
        proc.kill()
        pytest.fail("Headless Nuke did not start within 30 seconds")

    yield proc

    proc.kill()
    proc.wait(timeout=10)


@pytest.fixture
def integration_conn(nuke_process):
    """Provide a connection to the running headless Nuke."""
    conn = NukeConnection("127.0.0.1", NUKE_PORT)
    conn.connect()
    yield conn
    # Clear script state between tests
    try:
        conn.send({"type": "execute_python", "params": {"code": "nuke.scriptClear()"}})
    except Exception:
        pass
    conn.disconnect()
