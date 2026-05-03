import sqlite3
from typing import List, Dict

DB_PATH = "carp_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            age INTEGER,
            years_in_pro INTEGER,
            current_performance REAL, 
            potential_score REAL,
            batting_avg REAL,
            home_runs INTEGER,
            era REAL,
            image_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_players(players_data: List[Dict]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 簡単のため、今回は都度クリアして入れ直す設計とします
    cursor.execute('DELETE FROM players')
    
    for p in players_data:
        cursor.execute('''
            INSERT INTO players (name, position, age, years_in_pro, current_performance, potential_score, batting_avg, home_runs, era, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (p.get('name'), p.get('position'), p.get('age'), p.get('years_in_pro'), 
              p.get('current_performance'), p.get('potential_score'), 
              p.get('batting_avg'), p.get('home_runs'), p.get('era'), p.get('image_url')))
    
    conn.commit()
    conn.close()

def get_all_players() -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM players')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
