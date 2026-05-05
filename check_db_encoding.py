import sqlite3
import os

db_path = 'CarpAnalytics/backend/carp_data.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT name, team FROM players LIMIT 5')
rows = cursor.fetchall()

for name, team in rows:
    print(f"Name: {name} (Hex: {name.encode('utf-8').hex()})")
    print(f"Team: {team} (Hex: {team.encode('utf-8').hex()})")
    print("-" * 20)

conn.close()
