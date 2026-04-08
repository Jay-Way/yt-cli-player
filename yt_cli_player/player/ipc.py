import json
import os
import socket
import time
from yt_cli_player.config import IPC_SOCKET_PATH


def wait_for_socket(timeout: float = 5.0) -> bool:
    """Poll until the mpv IPC socket appears or timeout elapses."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if os.path.exists(IPC_SOCKET_PATH):
            return True
        time.sleep(0.1)
    return False


class MpvIPC:
    def __init__(self):
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.connect(IPC_SOCKET_PATH)
        self._sock.settimeout(1.0)
        self._request_id = 0
        self._buf = b""

    def _send(self, command: list) -> dict:
        self._request_id += 1
        req_id = self._request_id
        msg = json.dumps({"command": command, "request_id": req_id}) + "\n"
        try:
            self._sock.sendall(msg.encode())
        except OSError:
            return {}
        # Read responses until we find ours (mpv sends async events too)
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                self._buf += chunk
            except socket.timeout:
                pass
            while b"\n" in self._buf:
                line, self._buf = self._buf.split(b"\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    resp = json.loads(line)
                    if resp.get("request_id") == req_id:
                        return resp
                except json.JSONDecodeError:
                    pass
        return {}

    def get_property(self, name: str):
        return self._send(["get_property", name]).get("data")

    def set_property(self, name: str, value) -> None:
        self._send(["set_property", name, value])

    def command(self, *args) -> None:
        self._send(list(args))

    def toggle_pause(self) -> None:
        self.command("cycle", "pause")

    def quit(self) -> None:
        self.command("quit")

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass
