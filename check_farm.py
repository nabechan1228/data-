import sqlite3
import json
import os

def check_farm_integration():
    # 正しいDBパス
    db_path = r'c:\Users\nabe4\data-\CarpAnalytics\backend\carp_data.db'
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT name, batting_avg, farm_stats_json, current_performance FROM players WHERE farm_stats_json != '{}' LIMIT 10"
    rows = conn.execute(query).fetchall()
    
    if not rows:
        print("No players found with farm stats.")
        return

    for r in rows:
        farm = json.loads(r['farm_stats_json'])
        print(f"Name: {r['name']}")
        print(f"  1st Avg: {r['batting_avg']}")
        print(f"  Farm stats: {farm}")
        print(f"  Perf Score: {r['current_performance']}")
        print("-" * 20)

if __name__ == "__main__":
    check_farm_integration()
