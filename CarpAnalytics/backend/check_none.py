import sqlite3
import os

DB_PATH = r"backend\carp_data.db"

def check_none():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT player_name, team, stat_type, team_games, plate_appearances FROM season_stats_2026 WHERE team_games IS NULL AND stat_type="batting"')
    rows = cursor.fetchall()
    print(f"Found {len(rows)} batting records with NULL team_games")
    for row in rows[:20]:
        print(dict(row))
    conn.close()

if __name__ == "__main__":
    check_none()
