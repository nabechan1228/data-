import sqlite3
from typing import List, Dict
import os

# 絶対パスでDBを指定（ディレクトリトラバーサル対策）
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "carp_data.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS players')
    cursor.execute('''
        CREATE TABLE players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team TEXT NOT NULL,
            name TEXT NOT NULL,
            position TEXT NOT NULL,
            age INTEGER,
            years_in_pro INTEGER,
            current_performance REAL, 
            potential_score REAL,
            batting_avg REAL,
            home_runs INTEGER,
            era REAL,
            defense INTEGER,
            speed INTEGER,
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
            INSERT INTO players (team, name, position, age, years_in_pro, current_performance, potential_score, batting_avg, home_runs, era, defense, speed, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (p.get('team'), p.get('name'), p.get('position'), p.get('age'), p.get('years_in_pro'), 
              p.get('current_performance'), p.get('potential_score'), 
              p.get('batting_avg'), p.get('home_runs'), p.get('era'), 
              p.get('defense'), p.get('speed'), p.get('image_url')))
    
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
