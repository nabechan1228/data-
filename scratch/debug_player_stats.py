import sqlite3
import os
import json

db_path = os.path.join('CarpAnalytics', 'backend', 'carp_data.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

player_name = '黒原拓未'
print(f"--- Debugging {player_name} ---")

# Check players table
cursor.execute("SELECT * FROM players WHERE name LIKE ?", (f'%{player_name}%',))
row = cursor.fetchone()
if row:
    p = dict(row)
    print(f"Player ID: {p['id']}")
    print(f"Name: {p['name']}")
    print(f"Position: {p['position']}")
    print(f"Team: {p['team']}")
else:
    print("Player not found in players table.")

# Check season_stats table
cursor.execute("SELECT * FROM season_stats_2026 WHERE player_name LIKE ?", (f'%{player_name}%',))
row = cursor.fetchone()
if row:
    s = dict(row)
    print(f"Stat Type: {s['stat_type']}")
    print(f"ERA: {s['era']}")
    print(f"Wins: {s['wins']}")
else:
    print("Stats not found in season_stats_2026 table.")

# Check all pitchers for Hiroshima
print("\n--- All Pitchers for Hiroshima ---")
cursor.execute("SELECT name, position FROM players WHERE team = '広島東洋カープ' AND position LIKE '%投手%'")
rows = cursor.fetchall()
print(f"Count: {len(rows)}")
for r in rows[:10]:
    print(f"  {r['name']} ({r['position']})")

conn.close()
