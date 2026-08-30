import socket
import time
import pytest
from micro_server import MicroRpcServer

def test_rapid_rpc_echo():
    """
    Test Case 10: Hard Ambiguous Case (Socket Address TIME_WAIT Port Collision)
    Taxonomy: hard_ambiguous_case
    Description:
    Symptom: Client gets OSError [Errno 10048/98] (Address already in use) or TimeoutError connecting to server.
    Apparent Cause: Naive inspection suggests "timing/sleep issue" or "server didn't start in time".
    Real Root Cause: Server socket bind lacks SO_REUSEADDR, so rapid stop/start cycles fail due to TCP TIME_WAIT.
    """
    server = MicroRpcServer(port=8989)
    try:
        server.start()
        time.sleep(0.01)

        # Client connects
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(0.5)
        client.connect(("127.0.0.1", 8989))
        client.sendall(b"HELLO")
        resp = client.recv(1024)
        client.close()

        assert resp == b"PONG:HELLO"
    finally:
        server.stop()
