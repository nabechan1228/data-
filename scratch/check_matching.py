import sqlite3
import os

db_path = os.path.join('CarpAnalytics', 'backend', 'carp_data.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

player_name = '黒原'
cursor.execute("SELECT * FROM players WHERE name LIKE ?", (f'%{player_name}%',))
row = cursor.fetchone()
if row:
    p = dict(row)
    print(f"Player: {p['name']}, ERA: {p['era']}, Position: {p['position']}")
    
    # Check stats matching
    from lineup_engine import LineupOptimizer
    opt = LineupOptimizer(db_path)
    # Mocking the normalize_name logic
    def normalize_name(n):
        return n.replace(' ', '').replace('　', '')
    
    norm_name = normalize_name(p['name'])
    print(f"Normalized Name: {norm_name}")
    
    cursor.execute("SELECT * FROM season_stats_2026 WHERE replace(replace(player_name, ' ', ''), '　', '') = ?", (norm_name,))
    stat_row = cursor.fetchone()
    if stat_row:
        s = dict(stat_row)
        print(f"Stat found! ERA: {s['era']}")
    else:
        print("Stat NOT found in season_stats_2026.")
        # Let's list some names from stats to see why
        cursor.execute("SELECT player_name FROM season_stats_2026 LIMIT 10")
        print("Sample names in stats:")
        for r in cursor.fetchall():
            print(f"  '{r[0]}'")

conn.close()
