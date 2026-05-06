import sqlite3
import os
import json

# 絶対パスでDBを指定
_BASE_DIR = r"c:\Users\nabe4\data-\CarpAnalytics\backend"
DB_PATH = os.path.join(_BASE_DIR, "carp_data.db")

def check_kuribayashi():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- Players Table ---")
    # 栗林 良吏 を検索
    cursor.execute("SELECT * FROM players WHERE name LIKE '%栗林%'")
    rows = cursor.fetchall()
    for row in rows:
        d = dict(row)
        print(f"Name: {d['name']}, Team: {d['team']}")
        print(f"Current Performance: {d['current_performance']}, Potential Score: {d['potential_score']}")
        print(f"Perf Axes: {d['perf_axes_json']}")
        print(f"Pot Axes: {d['pot_axes_json']}")
        print("-" * 20)

    print("\n--- Season Stats Table ---")
    cursor.execute("SELECT * FROM season_stats_2026 WHERE player_name LIKE '%栗林%'")
    rows = cursor.fetchall()
    for row in rows:
        d = dict(row)
        print(f"Name: {d['player_name']}, Team: {d['team']}, Type: {d['stat_type']}")
        print(f"ERA: {d['era']}, Wins: {d['wins']}, Saves: {d['saves']}, SO: {d['strikeouts']}")
        print("-" * 20)

    print("\n--- Snapshots Table ---")
    cursor.execute("SELECT * FROM player_daily_snapshots WHERE player_name LIKE '%栗林%' ORDER BY snapshot_date DESC")
    rows = cursor.fetchall()
    for row in rows:
        d = dict(row)
        print(f"Date: {d['snapshot_date']}, Name: {d['player_name']}, OPS: {d['ops']}, K9: {d['k9']}")

    conn.close()

if __name__ == "__main__":
    check_kuribayashi()
