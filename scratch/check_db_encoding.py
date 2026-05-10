import sqlite3
import os

_BASE_DIR = r"c:\Users\nabe4\data-\CarpAnalytics\backend"
DB_PATH = os.path.join(_BASE_DIR, "carp_data.db")

def check_names():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM players WHERE team = '阪神タイガース' LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        name = row[0]
        print(f"Name: {name}")
        print(f"Hex: {name.encode('utf-8').hex()}")
        try:
            print(f"As CP932 decoded from latin1: {name.encode('latin1').decode('cp932')}")
        except:
            pass
        print("-" * 20)
    conn.close()

if __name__ == "__main__":
    check_names()
