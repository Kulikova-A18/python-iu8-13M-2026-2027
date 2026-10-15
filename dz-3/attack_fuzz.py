# attack_fuzz.py
import random
import string
from bank_client import BankClient

COMMANDS = ["LOGIN", "BALANCE", "TRANSFER", "HISTORY", "ADMIN", "HELP", "QUIT", ""]

def rand_token(n=12):
    return "".join(random.choices(string.printable, k=n))


cases = [
    "LOGIN",
    "LOGIN onlylogin",
    "LOGIN a b c d e",
    "TRANSFER",
    "TRANSFER abc xyz",
    "TRANSFER 1 -999999999999999999999",
    "TRANSFER 2 0.000000000000000001",
    "HISTORY -1",
    "HISTORY 99999999999",
    "ADMIN " + rand_token(50),
    rand_token(200),
]

c = BankClient()
c.cmd("LOGIN alice qwerty")

for case in cases:
    try:
        resp = c.cmd(case)
        print(f"{case[:60]!r:62} -> {resp[:100]}")
    except Exception as e:
        print(f"{case[:60]!r:62} -> EXC {e}")

c.close()
