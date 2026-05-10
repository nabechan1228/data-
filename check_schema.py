import sqlite3

conn = sqlite3.connect('CarpAnalytics/backend/carp_data.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(players)")
for row in cursor.fetchall():
    print(row)
conn.close()
