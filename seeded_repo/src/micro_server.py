import socket
import threading
import time

class MicroRpcServer:
    """
    Embedded test RPC server.
    Flake Cause (Hard Ambiguous Case):
    1. Server binds socket inside background thread with variable startup latency (5-25ms).
    2. Client test uses a fragile hardcoded sleep(0.01) before connecting.
    3. Server socket bind lacks a synchronization event or dynamic ephemeral port.
    """
    def __init__(self, port: int = 8989):
        self.port = port
        self.sock = None
        self.is_running = False
        self._thread = None

    def start(self):
        self.is_running = True

        def _serve():
            # Variable asynchronous startup delay (simulating heavy server boot)
            time.sleep(0.005 + (0.015 * (time.time() % 1)))
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind(("127.0.0.1", self.port))
            self.sock.listen(1)
            self.sock.settimeout(0.2)
            while self.is_running:
                try:
                    client, _ = self.sock.accept()
                    data = client.recv(1024)
                    client.sendall(b"PONG:" + data)
                    client.close()
                except (socket.timeout, OSError):
                    continue

        self._thread = threading.Thread(target=_serve, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
