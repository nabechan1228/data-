import sqlite3
import os

db_path = os.path.join('CarpAnalytics', 'backend', 'carp_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT player_name FROM season_stats_2026")
all_names = [r[0] for r in cursor.fetchall()]

target = '黒原'
found = [n for n in all_names if target in n]

print(f"Searching for '{target}'...")
if found:
    for f in found:
        print(f"Found: '{f}' (Hex: {f.encode('utf-8').hex()})")
else:
    print("Not found at all in stats table.")

conn.close()
