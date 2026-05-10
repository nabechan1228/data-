import sqlite3
import os

db_path = os.path.join('CarpAnalytics', 'backend', 'carp_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- Players Table ---")
cursor.execute("SELECT name FROM players WHERE name LIKE '%黒原%'")
rows = cursor.fetchall()
for r in rows:
    name = r[0]
    print(f"Name: {name}, Hex: {name.encode('utf-8').hex()}")

print("\n--- Season Stats Table ---")
cursor.execute("SELECT player_name FROM season_stats_2026 WHERE player_name LIKE '%黒原%'")
rows = cursor.fetchall()
for r in rows:
    name = r[0]
    print(f"Name: {name}, Hex: {name.encode('utf-8').hex()}")

conn.close()
