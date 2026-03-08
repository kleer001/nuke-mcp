"""Mock Nuke socket for offline development and testing.

Simulates the Nuke addon's socket behavior without Nuke running.
Maintains minimal internal state so sequential commands produce coherent responses.
"""

import json
import threading
import socket


class MockNukeState:
    """Minimal simulated Nuke scene state."""

    def __init__(self, nuke_version: str = "17.0v1", variant: str = "NukeX"):
        self.nuke_version = nuke_version
        self.variant = variant
        self.nodes: dict[str, dict] = {}
        self.connections: list[dict] = []
        self.frame_range = [1001, 1100]
        self.fps = 24.0
        self.colorspace = "ACES"
        self.resolution = [1920, 1080]
        self.script_name = "untitled.nk"
        self._next_id = 1

    def handshake(self) -> dict:
        return {
            "type": "handshake",
            "nuke_version": self.nuke_version,
            "variant": self.variant,
            "pid": 99999,
        }

    def handle(self, command: dict) -> dict:
        cmd_type = command.get("type", "")
        params = command.get("params", {})
        handler = getattr(self, f"_cmd_{cmd_type}", None)
        if not handler:
            return {"status": "error", "error": f"Unknown command: {cmd_type}"}
        try:
            return handler(params)
        except Exception as e:
            return {"status": "error", "error": f"{type(e).__name__}: {e}"}

    def _cmd_ping(self, params: dict) -> dict:
        return {"status": "ok", "result": "pong"}

    def _cmd_get_script_info(self, params: dict) -> dict:
        return {
            "status": "ok",
            "result": {
                "name": self.script_name,
                "frame_range": self.frame_range,
                "fps": self.fps,
                "format": f"{self.resolution[0]} {self.resolution[1]}",
                "colorspace": self.colorspace,
                "node_count": len(self.nodes),
            },
        }

    def _cmd_get_node_info(self, params: dict) -> dict:
        name = params["node_name"]
        node = self.nodes.get(name)
        if not node:
            return {"status": "error", "error": f"Node '{name}' not found"}

        inputs = [
            c["output"]
            for c in self.connections
            if c["input"] == name
        ]
        return {
            "status": "ok",
            "result": {
                "name": name,
                "class": node["class"],
                "xpos": node["xpos"],
                "ypos": node["ypos"],
                "inputs": inputs,
                "knobs": node.get("knobs", {}),
            },
        }

    def _cmd_create_node(self, params: dict) -> dict:
        node_class = params["node_class"]
        if params.get("name"):
            name = params["name"]
        else:
            name = f"{node_class}{self._next_id}"
            self._next_id += 1
        position = params.get("position", [0, 0])

        self.nodes[name] = {
            "class": node_class,
            "xpos": position[0],
            "ypos": position[1],
            "knobs": params.get("knobs", {}),
        }
        return {
            "status": "ok",
            "result": {
                "name": name,
                "class": node_class,
                "xpos": position[0],
                "ypos": position[1],
            },
        }

    def _cmd_modify_node(self, params: dict) -> dict:
        name = params["node_name"]
        node = self.nodes.get(name)
        if not node:
            return {"status": "error", "error": f"Node '{name}' not found"}

        for k, v in params["knobs"].items():
            node.setdefault("knobs", {})[k] = v

        return {"status": "ok", "result": {"name": name, "modified_knobs": list(params["knobs"].keys())}}

    def _cmd_delete_node(self, params: dict) -> dict:
        name = params["node_name"]
        node = self.nodes.get(name)
        if not node:
            return {"status": "error", "error": f"Node '{name}' not found"}

        node_class = node["class"]
        del self.nodes[name]
        self.connections = [
            c for c in self.connections if c["input"] != name and c["output"] != name
        ]
        return {"status": "ok", "result": {"deleted": name, "class": node_class}}

    def _cmd_connect_nodes(self, params: dict) -> dict:
        output_name = params["output_node"]
        input_name = params["input_node"]
        input_index = params.get("input_index", 0)

        if output_name not in self.nodes:
            return {"status": "error", "error": f"Node '{output_name}' not found"}
        if input_name not in self.nodes:
            return {"status": "error", "error": f"Node '{input_name}' not found"}

        self.connections.append({
            "output": output_name,
            "input": input_name,
            "input_index": input_index,
        })
        return {
            "status": "ok",
            "result": {
                "output": output_name,
                "input": input_name,
                "input_index": input_index,
            },
        }

    def _cmd_position_node(self, params: dict) -> dict:
        name = params["node_name"]
        node = self.nodes.get(name)
        if not node:
            return {"status": "error", "error": f"Node '{name}' not found"}

        node["xpos"] = int(params["x"])
        node["ypos"] = int(params["y"])
        return {"status": "ok", "result": {"name": name, "xpos": node["xpos"], "ypos": node["ypos"]}}

    def _cmd_auto_layout(self, params: dict) -> dict:
        node_names = params.get("node_names")
        if node_names:
            # Validate node names exist, matching addon behavior
            valid = [n for n in node_names if n in self.nodes]
            if not valid:
                return {"status": "error", "error": "No nodes to layout"}
            count = len(valid)
        else:
            if not self.nodes:
                return {"status": "error", "error": "No nodes to layout"}
            count = len(self.nodes)
        return {"status": "ok", "result": {"laid_out": count}}

    def _cmd_execute_python(self, params: dict) -> dict:
        return {"status": "ok", "result": f"[mock] executed: {params['code'][:100]}"}

    def _cmd_load_script(self, params: dict) -> dict:
        self.script_name = params["path"]
        return {"status": "ok", "result": {"loaded": params["path"], "node_count": len(self.nodes)}}

    def _cmd_save_script(self, params: dict) -> dict:
        path = params.get("path", self.script_name)
        self.script_name = path
        return {"status": "ok", "result": {"saved": path}}

    def _cmd_set_project_settings(self, params: dict) -> dict:
        modified = []
        if "fps" in params:
            self.fps = float(params["fps"])
            modified.append("fps")
        if "colorspace" in params:
            self.colorspace = params["colorspace"]
            modified.append("colorspace")
        if "resolution" in params:
            self.resolution = list(params["resolution"])
            modified.append("resolution")
        return {"status": "ok", "result": {"modified": modified}}

    def _cmd_set_frame_range(self, params: dict) -> dict:
        first = int(params["first"])
        last = int(params["last"])
        if first > last:
            return {"status": "error", "error": f"first ({first}) must be <= last ({last})"}
        self.frame_range = [first, last]
        return {
            "status": "ok",
            "result": {"first_frame": self.frame_range[0], "last_frame": self.frame_range[1]},
        }


class MockNukeServer:
    """A mock TCP server that behaves like the Nuke addon for offline development."""

    def __init__(
        self,
        port: int = 54321,
        nuke_version: str = "17.0v1",
        variant: str = "NukeX",
    ):
        self.port = port
        self.state = MockNukeState(nuke_version, variant)
        self._server_sock: socket.socket | None = None
        self._running = False
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()

    def start(self):
        if self._running:
            return
        self._running = True
        self._ready.clear()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5.0)

    def stop(self):
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass

    def _serve(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.settimeout(1.0)
        self._server_sock.bind(("127.0.0.1", self.port))
        self._server_sock.listen(1)
        self._ready.set()

        while self._running:
            try:
                client, _ = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            self._handle_client(client)

    def _handle_client(self, client: socket.socket):
        client.settimeout(None)
        # Send handshake
        self._send(client, self.state.handshake())

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
                response = self.state.handle(command)
                self._send(client, response)

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
