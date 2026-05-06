import sqlite3
import json

db_path = r'CarpAnalytics\backend\carp_data.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name, team FROM players LIMIT 20")
data = cursor.fetchall()

result = []
for row in data:
    result.append({"name": row[0], "team": row[1]})

with open('db_check_result.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Saved {len(result)} records to db_check_result.json")
conn.close()
