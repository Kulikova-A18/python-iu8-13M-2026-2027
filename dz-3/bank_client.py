# bank_client.py
import socket

HOST = "127.0.0.1"
PORT = 9999


class BankClient:
    def __init__(self, host=HOST, port=PORT, timeout=5):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((host, port))
        self.sock.recv(4096)

    def cmd(self, line: str) -> str:
        self.sock.sendall(line.encode() + b"\n")
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        return buf.decode(errors="ignore").strip()

    def close(self):
        try:
            self.cmd("QUIT")
        finally:
            self.sock.close()
