import sqlite3
import json

def check_fielding_db():
    db_path = r'c:\Users\nabe4\data-\CarpAnalytics\backend\carp_data.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT name, fielding_json FROM players WHERE fielding_json != '{}' LIMIT 10"
    rows = conn.execute(query).fetchall()
    if not rows:
        print("No players with fielding data found.")
    for r in rows:
        print(f"Name: {r['name']}, Data: {r['fielding_json']}")

if __name__ == "__main__":
    check_fielding_db()
