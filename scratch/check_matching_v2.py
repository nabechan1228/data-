import sqlite3
import os
import sys

# Add backend to sys.path
backend_path = os.path.join('CarpAnalytics', 'backend')
sys.path.append(backend_path)

db_path = os.path.join(backend_path, 'carp_data.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

def normalize_name(n):
    return n.replace(' ', '').replace('　', '')

player_name = '黒原'
cursor.execute("SELECT * FROM players WHERE name LIKE ?", (f'%{player_name}%',))
row = cursor.fetchone()
if row:
    p = dict(row)
    print(f"Player: {p['name']}, ERA: {p['era']}, Position: {p['position']}")
    
    norm_name = normalize_name(p['name'])
    print(f"Normalized Name: {norm_name}")
    
    # Check if this name exists in season_stats_2026
    cursor.execute("SELECT player_name, era FROM season_stats_2026")
    stats = cursor.fetchall()
    found = False
    for s in stats:
        if normalize_name(s['player_name']) == norm_name:
            print(f"MATCH FOUND in stats! Original: {s['player_name']}, ERA: {s['era']}")
            found = True
            break
    if not found:
        print("No match found in season_stats_2026.")
        print("Listing first 10 names from stats for comparison:")
        for s in stats[:10]:
            print(f"  '{s['player_name']}' (Hex: {s['player_name'].encode('utf-8').hex()})")

conn.close()
