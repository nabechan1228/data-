import sqlite3
import os

db_path = os.path.join('CarpAnalytics', 'backend', 'carp_data.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM players LIMIT 5")
rows = cursor.fetchall()
for r in rows:
    name = r[0]
    print(f"Name: {name}")
    try:
        print(f"Hex: {name.encode('utf-8').hex()}")
    except:
        print("Hex: error")
conn.close()
