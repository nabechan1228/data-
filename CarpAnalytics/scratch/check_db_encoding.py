import sqlite3
import os

db_path = r'c:\Users\nabe4\data-\CarpAnalytics\backend\carp_data.db'
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- Teams ---")
    cursor.execute("SELECT DISTINCT team FROM players")
    teams = cursor.fetchall()
    if not teams:
        print("No players found in database.")
    for row in teams:
        print(row[0])
        
    print("\n--- Sample Players ---")
    cursor.execute("SELECT name, team FROM players LIMIT 10")
    for row in cursor.fetchall():
        print(f"{row[0]} ({row[1]})")
        
    conn.close()
