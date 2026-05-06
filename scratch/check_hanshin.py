import sqlite3
import os
import json

_BASE_DIR = r"c:\Users\nabe4\data-\CarpAnalytics\backend"
DB_PATH = os.path.join(_BASE_DIR, "carp_data.db")

def check_hanshin_players():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    names = ["佐藤", "森下"]
    
    print("--- Players Table ---")
    for name in names:
        cursor.execute("SELECT * FROM players WHERE name LIKE ? AND team = '阪神タイガース'", (f'%{name}%',))
        rows = cursor.fetchall()
        for row in rows:
            d = dict(row)
            print(f"Name: {d['name']}, Team: {d['team']}, Pos: {d['position']}, Age: {d['age']}")
            print(f"Current Performance: {d['current_performance']}, Potential Score: {d['potential_score']}")
            print(f"Batting Avg: {d['batting_avg']}, HR: {d['home_runs']}, ERA: {d['era']}")
            print(f"Perf Axes: {d['perf_axes_json']}")
            print("-" * 20)

    print("\n--- Season Stats Table ---")
    for name in names:
        cursor.execute("SELECT * FROM season_stats_2026 WHERE player_name LIKE ? AND team = '阪神タイガース'", (f'%{name}%',))
        rows = cursor.fetchall()
        for row in rows:
            d = dict(row)
            print(f"Name: {d['player_name']}, Type: {d['stat_type']}, G: {d['games']}, AVG: {d['batting_avg']}, HR: {d['home_runs']}, OPS: {d['ops']}")
            print("-" * 20)

    conn.close()

if __name__ == "__main__":
    check_hanshin_players()
