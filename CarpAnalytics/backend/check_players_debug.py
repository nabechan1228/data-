import sqlite3
conn = sqlite3.connect('carp_data.db')
cursor = conn.cursor()
cursor.execute('SELECT name, team FROM players LIMIT 10')
for r in cursor.fetchall():
    print(r)
conn.close()
