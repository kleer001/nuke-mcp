"""execute_python in the Nuke addon, run outside Nuke with a stub module."""

import sys
import types

class _Stub:
    def __init__(self, *args, **kwargs):
        pass


def _stub_module(name):
    module = types.ModuleType(name)
    module.__getattr__ = lambda attr: _Stub
    return module


# The addon imports nuke and PySide at load time; neither exists outside Nuke.
for name in ("nuke", "PySide6", "PySide6.QtWidgets", "PySide6.QtCore", "PySide6.QtGui"):
    sys.modules.setdefault(name, _stub_module(name))
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent / "nuke_addon"))

import nuke_mcp_addon  # noqa: E402


def test_comprehension_sees_top_level_names():
    code = "names = ['a', 'b']\nprefix = 'n_'\nresult = [prefix + n for n in names]"
    response = nuke_mcp_addon._handle_execute_python({"code": code})
    assert response == {"status": "ok", "result": ["n_a", "n_b"]}


def test_function_sees_top_level_names():
    code = "scale = 3\ndef f(x):\n    return x * scale\nresult = f(2)"
    response = nuke_mcp_addon._handle_execute_python({"code": code})
    assert response == {"status": "ok", "result": 6}
