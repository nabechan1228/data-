import sqlite3
import os

_BASE_DIR = r"c:\Users\nabe4\data-\CarpAnalytics\backend"
DB_PATH = os.path.join(_BASE_DIR, "carp_data.db")

def check_hanshin_players():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    names = ["佐藤", "森下"]
    
    print("--- Season Stats Table ---")
    for name in names:
        # Use a more flexible search for names in case of encoding issues
        cursor.execute("SELECT * FROM season_stats_2026 WHERE player_name LIKE ? AND team = '阪神タイガース'", (f'%{name}%',))
        rows = cursor.fetchall()
        for row in rows:
            d = dict(row)
            print(f"Name: {d['player_name']}, G: {d['games']}, PA: {d['plate_appearances']}, AVG: {d['batting_avg']}, HR: {d['home_runs']}, OPS: {d['ops']}, TeamGames: {d['team_games']}")
            print("-" * 20)

    conn.close()

if __name__ == "__main__":
    check_hanshin_players()
