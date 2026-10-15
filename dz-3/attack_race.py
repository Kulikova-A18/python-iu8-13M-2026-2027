# attack_race.py
import threading
from bank_client import BankClient

TARGET_ID = 3
THREADS = 20
AMOUNT = 400
ITER = 10

results = []


def worker(n):
    try:
        c = BankClient()
        c.cmd("LOGIN alice qwerty")
        for i in range(ITER):
            r = c.cmd(f"TRANSFER {TARGET_ID} {AMOUNT} race_{n}_{i}")
            results.append(r)
        c.close()
    except Exception as e:
        results.append(f"ERR|{e}")


threads = [threading.Thread(target=worker, args=(n,)) for n in range(THREADS)]
for t in threads:
    t.start()
for t in threads:
    t.join()

ok = sum(1 for r in results if r.startswith("OK"))
err = sum(1 for r in results if r.startswith("ERR"))
print(f"Successful transfers: {ok}")
print(f"Rejected:             {err}")
print(f"Expected successful: no more than {5000 // AMOUNT} (based on alice's balance)")

c = BankClient()
print("alice login:", c.cmd("LOGIN alice qwerty"))
print("alice balance:", c.cmd("BALANCE"))
print("bob login:", c.cmd("LOGIN bob 12345"))
print("bob balance:  ", c.cmd("BALANCE"))
c.close()
