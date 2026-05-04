import sqlite3
import os

def check_player():
    db_path = os.path.join(os.getcwd(), 'CarpAnalytics', 'backend', 'carp_data.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # 精密に検索
    query = "SELECT player_name, ops, on_base_pct, slg_pct, stat_type FROM season_stats_2026 WHERE player_name LIKE '%西川%' AND team LIKE '%オリックス%'"
    rows = conn.execute(query).fetchall()
    for r in rows:
        print(f"Name: {repr(r['player_name'])}, OPS: {r['ops']}, OBP: {r['on_base_pct']}, SLG: {r['slg_pct']}")
    conn.close()

if __name__ == "__main__":
    check_player()
