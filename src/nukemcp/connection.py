"""Socket connection to the Nuke addon."""

import json
import socket
import time
import logging

log = logging.getLogger(__name__)

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 54321
RECV_BUFFER = 1024 * 1024  # 1MB


class NukeConnectionError(Exception):
    """Failed to connect or communicate with the Nuke addon."""


class NukeConnection:
    """Manages a TCP socket connection to the Nuke addon running inside Nuke.

    On connect, reads a handshake message containing Nuke version and variant info.
    Sends JSON commands and receives JSON responses.
    """

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
        self.host = host
        self.port = port
        self.sock: socket.socket | None = None
        self.handshake: dict | None = None
        self._buffer = b""

    def connect(self, retries: int = 3, base_delay: float = 1.0) -> dict:
        """Connect to the Nuke addon and return the handshake data.

        Retries with exponential backoff on failure.
        """
        last_error = None
        for attempt in range(retries):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(10.0)
                self.sock.connect((self.host, self.port))
                self._buffer = b""
                self.handshake = self._read_message()
                log.info(
                    "Connected to Nuke %s (%s) at %s:%d",
                    self.handshake.get("nuke_version", "unknown"),
                    self.handshake.get("variant", "unknown"),
                    self.host,
                    self.port,
                )
                return self.handshake
            except (OSError, json.JSONDecodeError, TimeoutError) as e:
                last_error = e
                self._close_socket()
                if attempt < retries - 1:
                    delay = base_delay * (2**attempt)
                    log.warning(
                        "Connection attempt %d failed: %s. Retrying in %.1fs...",
                        attempt + 1,
                        e,
                        delay,
                    )
                    time.sleep(delay)

        raise NukeConnectionError(
            f"Failed to connect to Nuke addon at {self.host}:{self.port} "
            f"after {retries} attempts: {last_error}"
        )

    def send(self, command: dict, timeout: float = 10.0) -> dict:
        """Send a JSON command and return the JSON response."""
        if not self.sock:
            raise NukeConnectionError("Not connected to Nuke addon")

        msg = json.dumps(command) + "\n"
        try:
            self.sock.settimeout(timeout)
            self.sock.sendall(msg.encode("utf-8"))
            return self._read_message()
        except (OSError, json.JSONDecodeError, TimeoutError) as e:
            self._close_socket()
            raise NukeConnectionError(f"Communication error: {e}") from e

    def disconnect(self):
        """Cleanly disconnect from the Nuke addon."""
        self._close_socket()
        self.handshake = None
        log.info("Disconnected from Nuke addon")

    @property
    def is_connected(self) -> bool:
        return self.sock is not None

    def _read_message(self) -> dict:
        """Read a newline-delimited JSON message from the socket."""
        while b"\n" not in self._buffer:
            chunk = self.sock.recv(RECV_BUFFER)
            if not chunk:
                self._close_socket()
                raise NukeConnectionError("Connection closed by Nuke addon")
            self._buffer += chunk

        line, self._buffer = self._buffer.split(b"\n", 1)
        return json.loads(line.decode("utf-8"))

    def _close_socket(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None
