import sqlite3
import os

db_path = r'c:\Users\nabe4\data-\CarpAnalytics\backend\carp_data.db'
out_path = r'c:\Users\nabe4\data-\CarpAnalytics\scratch\db_output_utf8.txt'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT team FROM players")
    teams = cursor.fetchall()
    
    with open(out_path, 'w', encoding='utf-8') as f:
        for row in teams:
            f.write(row[0] + '\n')
    conn.close()
    print(f"Written to {out_path}")
