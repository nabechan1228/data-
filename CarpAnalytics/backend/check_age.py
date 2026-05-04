import sqlite3
import os

db_path = 'backend/carp_data.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check Kozono
cursor.execute("SELECT name, age, years_in_pro FROM players WHERE name LIKE '%小園海斗%'")
rows = cursor.fetchall()
print("Kozono Check:")
for row in rows:
    print(dict(row))

# Check Saito Taichi (Rookie)
cursor.execute("SELECT name, age, years_in_pro FROM players WHERE name LIKE '%齊藤汰直%'")
rows = cursor.fetchall()
print("\nSaito Check (Rookie):")
for row in rows:
    print(dict(row))

# Check Akiyama Shogo
cursor.execute("SELECT name, age, years_in_pro FROM players WHERE name LIKE '%秋山翔吾%'")
rows = cursor.fetchall()
print("\nAkiyama Check:")
for row in rows:
    print(dict(row))

conn.close()
