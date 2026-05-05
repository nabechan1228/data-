import sqlite3
conn = sqlite3.connect('carp_data.db')
cursor = conn.cursor()
cursor.execute('SELECT player_name, team_games, plate_appearances, innings_pitched FROM season_stats_2026 LIMIT 10')
for r in cursor.fetchall():
    print(r)
conn.close()
