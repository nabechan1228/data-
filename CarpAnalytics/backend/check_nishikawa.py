import sqlite3

def check_player():
    conn = sqlite3.connect('CarpAnalytics/backend/carp_data.db')
    conn.row_factory = sqlite3.Row
    # 名前の一部で検索
    query = "SELECT * FROM season_stats_2026 WHERE player_name LIKE '%西川%'"
    rows = conn.execute(query).fetchall()
    for r in rows:
        print(f"Name: {r['player_name']}, Team: {r['team']}, OPS: {r['ops']}, Type: {r['stat_type']}")
    conn.close()

if __name__ == "__main__":
    check_player()
