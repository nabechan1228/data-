import sqlite3
import os

DB_PATH = r"backend\carp_data.db"

def check_one_none():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM season_stats_2026 WHERE team_games IS NULL AND stat_type="batting" LIMIT 1')
    row = cursor.fetchone()
    if row:
        print(dict(row))
    else:
        print("No such record found")
    conn.close()

if __name__ == "__main__":
    check_one_none()
