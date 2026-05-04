import sqlite3

def verify_arai():
    db_path = r'c:\Users\nabe4\data-\CarpAnalytics\backend\carp_data.db'
    conn = sqlite3.connect(db_path)
    # 新井監督が含まれていないか確認
    query = "SELECT name, position FROM players WHERE name LIKE '%新井%'"
    rows = conn.execute(query).fetchall()
    
    if rows:
        print(f"Still found: {rows}")
    else:
        print("No Arai found. Cleanup successful.")

if __name__ == "__main__":
    verify_arai()
