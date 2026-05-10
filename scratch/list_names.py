import sqlite3
import os

db_path = os.path.join('CarpAnalytics', 'backend', 'carp_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT player_name FROM season_stats_2026 LIMIT 20")
for row in cursor.fetchall():
    print(f"'{row[0]}'")
conn.close()
