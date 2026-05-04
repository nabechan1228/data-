import sqlite3
import os

def check_player():
    db_path = os.path.join(os.getcwd(), 'CarpAnalytics', 'backend', 'carp_data.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM season_stats_2026 WHERE player_name LIKE '%西川%'"
    rows = conn.execute(query).fetchall()
    for r in rows:
        print(f"Name: {r['player_name']}, Team: {r['team']}, OPS: {r['ops']}, Type: {r['stat_type']}")
    conn.close()

if __name__ == "__main__":
    check_player()
