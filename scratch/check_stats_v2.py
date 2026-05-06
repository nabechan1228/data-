import sqlite3
import os

db_path = os.path.join('CarpAnalytics', 'backend', 'carp_data.db')
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

player_name = '黒原拓未'
cursor.execute("SELECT * FROM season_stats_2026 WHERE player_name = ?", (player_name,))
row = cursor.fetchone()
if row:
    print(f"Stats for {player_name}:")
    for key in row.keys():
        print(f"  {key}: {row[key]}")
else:
    print(f"No stats found for {player_name}")

conn.close()
