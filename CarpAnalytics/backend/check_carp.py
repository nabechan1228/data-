import sqlite3
import os

DB_PATH = r"backend\carp_data.db"

def check_carp():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT player_name, team_games, plate_appearances FROM season_stats_2026 WHERE team LIKE "%広島%" AND stat_type="batting" LIMIT 10')
    rows = cursor.fetchall()
    for row in rows:
        print(dict(row))
    conn.close()

if __name__ == "__main__":
    check_carp()
