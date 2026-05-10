import sqlite3
import json

conn = sqlite3.connect('CarpAnalytics/backend/carp_data.db')
cursor = conn.cursor()
cursor.execute("SELECT name, position, fielding_json FROM players WHERE position LIKE '%外野手%' LIMIT 10")
for row in cursor.fetchall():
    print(f"{row[0]} ({row[1]}): {row[2]}")
conn.close()
