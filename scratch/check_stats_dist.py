import sqlite3
import os

db_path = os.path.join('CarpAnalytics', 'backend', 'carp_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT team, stat_type, count(*) FROM season_stats_2026 GROUP BY team, stat_type")
rows = cursor.fetchall()
print("Stats count per team and type:")
for r in rows:
    print(f"  Team: {r[0]}, Type: {r[1]}, Count: {r[2]}")

conn.close()
