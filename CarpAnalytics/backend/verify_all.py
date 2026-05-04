import sqlite3
import os

db_path = 'backend/carp_data.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

players = ['近本', '岡本和真', '佐藤輝明', '小園海斗', '村上宗隆']
for p in players:
    cursor.execute("SELECT team, name, age, years_in_pro FROM players WHERE name LIKE ?", (f'%{p}%',))
    rows = cursor.fetchall()
    print(f"--- {p} ---")
    for row in rows:
        print(dict(row))

conn.close()
