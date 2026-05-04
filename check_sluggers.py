import sqlite3
import json

def check_sluggers_score():
    db_path = r'c:\Users\nabe4\data-\CarpAnalytics\backend\carp_data.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    names = ['佐藤輝明', '森下翔太']
    for name in names:
        query = "SELECT name, perf_axes_json FROM players WHERE name LIKE ?"
        r = conn.execute(query, (f'%{name}%',)).fetchone()
        if r:
            axes = json.loads(r['perf_axes_json'])
            # Axes: パワー, ミート, 走力, 守備, 安定感
            print(f"Name: {r['name']}")
            print(f"  Power: {axes[0]:.1f}, Meet: {axes[1]:.1f}")
        else:
            print(f"Name: {name} not found in players table")

if __name__ == "__main__":
    check_sluggers_score()
