"""NukeMCP Addon — Socket server running inside Nuke.

This file runs inside Nuke's Python environment. It creates a TCP socket server
that listens for JSON commands from the NukeMCP MCP server, executes them in
Nuke's main thread, and returns structured JSON responses.

No external dependencies beyond what Nuke ships with.

Usage:
    In Nuke's Script Editor or init.py/menu.py:
        import nuke_mcp_addon
        nuke_mcp_addon.start()
"""

import json
import logging
import socket
import threading

log = logging.getLogger("NukeMCP")

DEFAULT_PORT = 54321

# ---------------------------------------------------------------------------
# PySide import (PySide6 for Nuke 16+, PySide2 fallback)
# ---------------------------------------------------------------------------
try:
    from PySide6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
    )
    from PySide6.QtCore import Qt, Signal, QObject
    from PySide6.QtGui import QTextCursor

    _PYSIDE6 = True
except ImportError:
    from PySide2.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
    )
    from PySide2.QtCore import Qt, Signal, QObject
    from PySide2.QtGui import QTextCursor

    _PYSIDE6 = False


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def _get_nuke():
    """Import nuke lazily so this module can be parsed outside Nuke for testing."""
    import nuke
    return nuke


def _handshake_data() -> dict:
    nuke = _get_nuke()
    version = nuke.NUKE_VERSION_STRING
    # Determine variant using standard nuke.env keys
    try:
        if nuke.env.get("studio"):
            variant = "NukeStudio"
        elif nuke.env.get("nukex"):
            variant = "NukeX"
        else:
            variant = "Nuke"
    except Exception:
        variant = "Nuke"

    return {
        "type": "handshake",
        "nuke_version": version,
        "variant": variant,
        "pid": __import__("os").getpid(),
    }


def _handle_ping(params: dict) -> dict:
    return {"status": "ok", "result": "pong"}


def _handle_get_script_info(params: dict) -> dict:
    nuke = _get_nuke()
    root = nuke.root()
    return {
        "status": "ok",
        "result": {
            "name": root.name(),
            "frame_range": [root["first_frame"].value(), root["last_frame"].value()],
            "fps": root["fps"].value(),
            "format": str(root.format()),
            "colorspace": root["colorManagement"].value(),
            "node_count": len(nuke.allNodes()),
        },
    }


def _handle_get_node_info(params: dict) -> dict:
    nuke = _get_nuke()
    name = params["node_name"]
    node = nuke.toNode(name)
    if not node:
        return {"status": "error", "error": f"Node '{name}' not found"}

    knobs = {}
    for knob_name in node.knobs():
        try:
            knobs[knob_name] = node[knob_name].value()
        except Exception:
            knobs[knob_name] = str(node[knob_name])

    inputs = []
    for i in range(node.inputs()):
        inp = node.input(i)
        inputs.append(inp.name() if inp else None)

    return {
        "status": "ok",
        "result": {
            "name": node.name(),
            "class": node.Class(),
            "xpos": node.xpos(),
            "ypos": node.ypos(),
            "inputs": inputs,
            "knobs": knobs,
        },
    }


def _handle_create_node(params: dict) -> dict:
    nuke = _get_nuke()
    node_class = params["node_class"]
    name = params.get("name")
    knobs = params.get("knobs", {})
    position = params.get("position")

    node = nuke.createNode(node_class, inpanel=False)
    if name:
        node.setName(name)
    for k, v in knobs.items():
        if k in node.knobs():
            node[k].setValue(v)
    if position:
        node.setXpos(int(position[0]))
        node.setYpos(int(position[1]))

    return {
        "status": "ok",
        "result": {
            "name": node.name(),
            "class": node.Class(),
            "xpos": node.xpos(),
            "ypos": node.ypos(),
        },
    }


def _handle_modify_node(params: dict) -> dict:
    nuke = _get_nuke()
    name = params["node_name"]
    knobs = params["knobs"]
    node = nuke.toNode(name)
    if not node:
        return {"status": "error", "error": f"Node '{name}' not found"}

    # Validate all knob names before modifying any
    node_knobs = node.knobs()
    for k in knobs:
        if k not in node_knobs:
            return {"status": "error", "error": f"Knob '{k}' not found on node '{name}'"}

    for k, v in knobs.items():
        node[k].setValue(v)

    return {"status": "ok", "result": {"name": node.name(), "modified_knobs": list(knobs.keys())}}


def _handle_delete_node(params: dict) -> dict:
    nuke = _get_nuke()
    name = params["node_name"]
    node = nuke.toNode(name)
    if not node:
        return {"status": "error", "error": f"Node '{name}' not found"}

    node_class = node.Class()
    nuke.delete(node)
    return {"status": "ok", "result": {"deleted": name, "class": node_class}}


def _handle_connect_nodes(params: dict) -> dict:
    nuke = _get_nuke()
    output_name = params["output_node"]
    input_name = params["input_node"]
    input_index = params.get("input_index", 0)

    output_node = nuke.toNode(output_name)
    input_node = nuke.toNode(input_name)
    if not output_node:
        return {"status": "error", "error": f"Node '{output_name}' not found"}
    if not input_node:
        return {"status": "error", "error": f"Node '{input_name}' not found"}

    input_node.setInput(input_index, output_node)
    return {
        "status": "ok",
        "result": {
            "output": output_node.name(),
            "input": input_node.name(),
            "input_index": input_index,
        },
    }


def _handle_position_node(params: dict) -> dict:
    nuke = _get_nuke()
    name = params["node_name"]
    node = nuke.toNode(name)
    if not node:
        return {"status": "error", "error": f"Node '{name}' not found"}

    node.setXpos(int(params["x"]))
    node.setYpos(int(params["y"]))
    return {"status": "ok", "result": {"name": node.name(), "xpos": node.xpos(), "ypos": node.ypos()}}


def _handle_auto_layout(params: dict) -> dict:
    nuke = _get_nuke()
    node_names = params.get("node_names")
    if node_names:
        nodes = [nuke.toNode(n) for n in node_names if nuke.toNode(n)]
    else:
        nodes = nuke.allNodes()

    if not nodes:
        return {"status": "error", "error": "No nodes to layout"}

    for n in nodes:
        nuke.autoplace(n)

    return {"status": "ok", "result": {"laid_out": len(nodes)}}


def _handle_execute_python(params: dict) -> dict:
    code = params["code"]
    local_vars = {}
    try:
        exec(code, {"nuke": _get_nuke(), "__builtins__": __builtins__}, local_vars)  # noqa: S102
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}
    # Return whatever was assigned to 'result' in the executed code, or None
    result = local_vars.get("result")
    # Try to serialize; fall back to str
    try:
        json.dumps(result)
    except (TypeError, ValueError):
        result = str(result)
    return {"status": "ok", "result": result}


def _handle_load_script(params: dict) -> dict:
    nuke = _get_nuke()
    path = params["path"]
    nuke.scriptOpen(path)
    return {"status": "ok", "result": {"loaded": path, "node_count": len(nuke.allNodes())}}


def _handle_save_script(params: dict) -> dict:
    nuke = _get_nuke()
    path = params.get("path")
    if path:
        nuke.scriptSaveAs(path)
    else:
        nuke.scriptSave()
        path = nuke.root().name()
    return {"status": "ok", "result": {"saved": path}}


def _handle_set_project_settings(params: dict) -> dict:
    nuke = _get_nuke()
    root = nuke.root()
    modified = []
    if "fps" in params:
        root["fps"].setValue(float(params["fps"]))
        modified.append("fps")
    if "colorspace" in params:
        root["colorManagement"].setValue(params["colorspace"])
        modified.append("colorspace")
    if "resolution" in params:
        w, h = params["resolution"]
        fmt = nuke.addFormat(f"{w} {h} custom")
        root["format"].setValue(fmt)
        modified.append("resolution")
    return {"status": "ok", "result": {"modified": modified}}


def _handle_set_frame_range(params: dict) -> dict:
    nuke = _get_nuke()
    first = int(params["first"])
    last = int(params["last"])
    if first > last:
        return {"status": "error", "error": f"first ({first}) must be <= last ({last})"}
    root = nuke.root()
    root["first_frame"].setValue(first)
    root["last_frame"].setValue(last)
    return {
        "status": "ok",
        "result": {"first_frame": first, "last_frame": last},
    }


# Command dispatch table
COMMANDS = {
    "ping": _handle_ping,
    "get_script_info": _handle_get_script_info,
    "get_node_info": _handle_get_node_info,
    "create_node": _handle_create_node,
    "modify_node": _handle_modify_node,
    "delete_node": _handle_delete_node,
    "connect_nodes": _handle_connect_nodes,
    "position_node": _handle_position_node,
    "auto_layout": _handle_auto_layout,
    "execute_python": _handle_execute_python,
    "load_script": _handle_load_script,
    "save_script": _handle_save_script,
    "set_project_settings": _handle_set_project_settings,
    "set_frame_range": _handle_set_frame_range,
}


# ---------------------------------------------------------------------------
# Socket server
# ---------------------------------------------------------------------------

class _Signaller(QObject):
    """Bridge for emitting Qt signals from the socket thread."""
    log_signal = Signal(str)


class NukeMCPServer:
    """TCP socket server that listens for JSON commands from the MCP server."""

    def __init__(self, port: int = DEFAULT_PORT):
        self.port = port
        self._server_sock: socket.socket | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._signaller = _Signaller()

    @property
    def on_log(self):
        return self._signaller.log_signal

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        log.info("NukeMCP server started on port %d", self.port)

    def stop(self):
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass
            self._server_sock = None
        log.info("NukeMCP server stopped")

    def _serve(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.settimeout(1.0)
        self._server_sock.bind(("127.0.0.1", self.port))
        self._server_sock.listen(1)
        self._emit_log(f"Listening on port {self.port}")

        while self._running:
            try:
                client, addr = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            self._emit_log(f"Client connected from {addr[0]}:{addr[1]}")
            self._handle_client(client)
            self._emit_log("Client disconnected")

    def _handle_client(self, client: socket.socket):
        nuke = _get_nuke()
        client.settimeout(None)

        # Send handshake
        handshake = nuke.executeInMainThread(_handshake_data)
        if not isinstance(handshake, dict):
            try:
                client.close()
            except OSError:
                pass
            return
        self._send(client, handshake)

        buffer = b""
        while self._running:
            try:
                chunk = client.recv(1024 * 1024)
            except OSError:
                break
            if not chunk:
                break

            buffer += chunk
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                try:
                    command = json.loads(line.decode("utf-8"))
                except json.JSONDecodeError as e:
                    self._send(client, {"status": "error", "error": f"Invalid JSON: {e}"})
                    continue

                cmd_type = command.get("type", "")
                params = command.get("params", {})
                self._emit_log(f"<- {cmd_type}")

                handler = COMMANDS.get(cmd_type)
                if not handler:
                    response = {"status": "error", "error": f"Unknown command: {cmd_type}"}
                else:
                    try:
                        response = nuke.executeInMainThread(handler, args=(params,))
                    except Exception as e:
                        response = {"status": "error", "error": f"{type(e).__name__}: {e}"}

                self._send(client, response)
                self._emit_log(f"-> {response.get('status', '?')}")

        try:
            client.close()
        except OSError:
            pass

    def _send(self, client: socket.socket, data: dict):
        msg = json.dumps(data) + "\n"
        try:
            client.sendall(msg.encode("utf-8"))
        except OSError:
            pass

    def _emit_log(self, msg: str):
        log.info(msg)
        self._signaller.log_signal.emit(msg)


# ---------------------------------------------------------------------------
# Panel UI
# ---------------------------------------------------------------------------

class NukeMCPPanel(QWidget):
    """Dockable panel showing NukeMCP server status and log."""

    def __init__(self, port: int = DEFAULT_PORT, parent=None):
        super().__init__(parent)
        self.setWindowTitle("NukeMCP")
        self.setMinimumWidth(300)
        self.setMinimumHeight(200)

        self._port = port
        self._server: NukeMCPServer | None = None

        # Status row
        status_layout = QHBoxLayout()
        self._status_label = QLabel("Stopped")
        self._port_label = QLabel(f"Port: {self._port}")
        self._toggle_btn = QPushButton("Start")
        self._toggle_btn.clicked.connect(self._toggle_server)
        status_layout.addWidget(self._status_label)
        status_layout.addStretch()
        status_layout.addWidget(self._port_label)
        status_layout.addWidget(self._toggle_btn)

        # Log area
        self._log = QTextEdit()
        self._log.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addLayout(status_layout)
        layout.addWidget(self._log)
        self.setLayout(layout)

    def _toggle_server(self):
        if self._server and self._server._running:
            self._server.stop()
            self._server = None
            self._status_label.setText("Stopped")
            self._toggle_btn.setText("Start")
            self._append_log("Server stopped")
        else:
            self._server = NukeMCPServer(self._port)
            self._server.on_log.connect(self._append_log)
            self._server.start()
            self._status_label.setText("Running")
            self._toggle_btn.setText("Stop")

    def _append_log(self, msg: str):
        self._log.append(msg)
        # Keep last 200 lines
        doc = self._log.document()
        if doc.blockCount() > 200:
            cursor = self._log.textCursor()
            # Use QTextCursor enum names compatible with both PySide2 and PySide6
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(
                QTextCursor.Down, QTextCursor.KeepAnchor, doc.blockCount() - 200
            )
            cursor.removeSelectedText()


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_panel = None


def start(port: int = DEFAULT_PORT):
    """Start the NukeMCP server and show the panel. Call from menu.py or Script Editor."""
    global _panel
    if _panel is None:
        _panel = NukeMCPPanel(port=port)
    _panel.show()
    _panel.raise_()
    # Auto-start the server
    if not (_panel._server and _panel._server._running):
        _panel._toggle_server()
