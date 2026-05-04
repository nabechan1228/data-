import sqlite3
import os

_BASE_DIR = r"c:\Users\nabe4\data-\CarpAnalytics\backend"
DB_PATH = os.path.join(_BASE_DIR, "carp_data.db")

def check_stats():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("--- Batting stats for players who might be pitchers or have low PA ---")
    cursor.execute('''
        SELECT player_name, team, plate_appearances, team_games, batting_avg
        FROM season_stats_2026
        WHERE stat_type = 'batting'
        LIMIT 20
    ''')
    for row in cursor.fetchall():
        print(dict(row))
        
    print("\n--- Summary of team_games ---")
    cursor.execute('SELECT team, MAX(team_games) as tg FROM season_stats_2026 GROUP BY team')
    for row in cursor.fetchall():
        print(dict(row))
        
    conn.close()

if __name__ == "__main__":
    check_stats()
