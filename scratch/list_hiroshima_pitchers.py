import sqlite3
import os

db_path = os.path.join('CarpAnalytics', 'backend', 'carp_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT player_name, era FROM season_stats_2026 WHERE team = '広島東洋カープ' AND stat_type = 'pitching'")
rows = cursor.fetchall()
print("Hiroshima Pitchers in stats:")
for r in rows:
    print(f"  '{r[0]}' (ERA: {r[1]})")

conn.close()
