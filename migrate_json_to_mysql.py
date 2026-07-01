import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import config
import database

json_path = "data/cities.json"
if not os.path.exists(json_path):
    print("No data/cities.json found — nothing to import.")
    sys.exit(0)

with open(json_path, encoding="utf-8") as f:
    cities = json.load(f)

for c in cities:
    database.save_city(c)
    print(f"Imported: {c.get('id')} — {c.get('name')}")

print(f"\nDone. {len(cities)} cities imported.")
