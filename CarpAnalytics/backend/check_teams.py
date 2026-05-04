import sqlite3
import os

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "carp_data.db")

def check_teams():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- season_stats_2026 table ---")
    cursor.execute("SELECT team, COUNT(*) FROM season_stats_2026 GROUP BY team")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Team: {row[0]}, Count: {row[1]}")
        
    print("\n--- players table ---")
    cursor.execute("SELECT team, COUNT(*) FROM players GROUP BY team")
    rows = cursor.fetchall()
    for row in rows:
        print(f"Team: {row[0]}, Count: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    check_teams()
