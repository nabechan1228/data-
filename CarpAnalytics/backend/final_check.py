import sqlite3
import os

DB_PATH = r"backend\carp_data.db"

def final_check():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    # 西武の投手を確認
    cursor.execute('SELECT player_name, team, team_games, innings_pitched FROM season_stats_2026 WHERE team="埼玉西武ライオンズ" AND stat_type="pitching" LIMIT 5')
    rows = cursor.fetchall()
    print("Seibu Pitchers:")
    for r in rows:
        print(dict(r))
        
    # 広島の打者を確認
    cursor.execute('SELECT player_name, team, team_games, plate_appearances FROM season_stats_2026 WHERE team="広島東洋カープ" AND stat_type="batting" LIMIT 5')
    rows = cursor.fetchall()
    print("\nCarp Batters:")
    for r in rows:
        print(dict(r))
    conn.close()

if __name__ == "__main__":
    final_check()
