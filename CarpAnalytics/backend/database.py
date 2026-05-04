import sqlite3
from typing import List, Dict, Optional
import os
import re
from datetime import datetime

# 絶対パスでDBを指定（ディレクトリトラバーサル対策）
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "carp_data.db")

def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
            putouts INTEGER,
            assists INTEGER,
            errors INTEGER,
            triples INTEGER,
            stolen_base_caught INTEGER,
            perf_area INTEGER,
            pot_area INTEGER,
            convergence_rate REAL,
            is_unbalanced BOOLEAN,
            perf_axes_json TEXT,
            pot_axes_json TEXT,
            fielding_json TEXT,
            farm_stats_json TEXT,
            is_awakened BOOLEAN,
            image_url TEXT,
            similarity_name TEXT,
            similarity_score REAL,
            ghost_axes_json TEXT
        )
    ''')
    # 今季成績テーブル（playersと分離して毎日軽量更新）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS season_stats_2026 (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name       TEXT NOT NULL,
            team              TEXT,
            league            TEXT,
            stat_type         TEXT NOT NULL,
            games             INTEGER,
            plate_appearances INTEGER,
            innings_pitched   REAL,
            team_games        INTEGER,
            batting_avg       REAL,
            hits              INTEGER,
            home_runs         INTEGER,
            rbi               INTEGER,
            stolen_bases      INTEGER,
            on_base_pct       REAL,
            slg_pct           REAL,
            ops               REAL,
            era               REAL,
            wins              INTEGER,
            losses            INTEGER,
            saves             INTEGER,
            holds             INTEGER,
            strikeouts        INTEGER,
            putouts           INTEGER,
            assists           INTEGER,
            errors            INTEGER,
            triples           INTEGER,
            stolen_base_caught INTEGER,
            last_updated      TEXT,
            UNIQUE(player_name, stat_type) ON CONFLICT REPLACE
        )
    ''')
    conn.commit()
    conn.close()

def ensure_stats_table():
    """season_stats_2026テーブルを作成し、必要に応じてカラムを追加（マイグレーション）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS season_stats_2026 (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name       TEXT NOT NULL,
            team              TEXT,
            league            TEXT,
            stat_type         TEXT NOT NULL,
            games             INTEGER,
            plate_appearances INTEGER,
            innings_pitched   REAL,
            team_games        INTEGER,
            batting_avg       REAL,
            hits              INTEGER,
            home_runs         INTEGER,
            rbi               INTEGER,
            stolen_bases      INTEGER,
            on_base_pct       REAL,
            slg_pct           REAL,
            ops               REAL,
            era               REAL,
            wins              INTEGER,
            losses            INTEGER,
            saves             INTEGER,
            holds             INTEGER,
            strikeouts        INTEGER,
            putouts           INTEGER,
            assists           INTEGER,
            errors            INTEGER,
            triples           INTEGER,
            stolen_base_caught INTEGER,
            last_updated      TEXT,
            UNIQUE(player_name, stat_type) ON CONFLICT REPLACE
        )
    ''')
    
    # 既存テーブルへのカラム追加（マイグレーション）
    cursor.execute("PRAGMA table_info(season_stats_2026)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = [
        ("league", "TEXT"),
        ("plate_appearances", "INTEGER"),
        ("innings_pitched", "REAL"),
        ("team_games", "INTEGER"),
        ("ops", "REAL"),
        ("putouts", "INTEGER"),
        ("assists", "INTEGER"),
        ("errors", "INTEGER"),
        ("triples", "INTEGER"),
        ("stolen_base_caught", "INTEGER"),
        ("walks", "INTEGER"),
        ("hits_allowed", "INTEGER")
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE season_stats_2026 ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to season_stats_2026")

    conn.commit()
    conn.close()

def save_players(players_data: List[Dict]):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM players')
    for p in players_data:
        cursor.execute('''
            INSERT INTO players (
                team, name, position, age, years_in_pro, current_performance, potential_score, 
                batting_avg, home_runs, era, defense, speed, putouts, assists, errors, triples, 
                stolen_base_caught, perf_area, pot_area, convergence_rate, is_unbalanced, 
                perf_axes_json, pot_axes_json, fielding_json, farm_stats_json, is_awakened, 
                image_url, similarity_name, similarity_score, ghost_axes_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (p.get('team'), p.get('name'), p.get('position'), p.get('age'), p.get('years_in_pro'), 
              p.get('current_performance'), p.get('potential_score'), 
              p.get('batting_avg'), p.get('home_runs'), p.get('era'), 
              p.get('defense'), p.get('speed'), p.get('putouts'), p.get('assists'), p.get('errors'), p.get('triples'), p.get('stolen_base_caught'),
              p.get('perf_area'), p.get('pot_area'), p.get('convergence_rate'), p.get('is_unbalanced'),
              p.get('perf_axes_json'), p.get('pot_axes_json'), p.get('fielding_json'), p.get('farm_stats_json'), p.get('is_awakened'), p.get('image_url'),
              p.get('similarity_name'), p.get('similarity_score'), p.get('ghost_axes_json')))
    conn.commit()
    conn.close()

def save_season_stats(stats_list: List[Dict]):
    """今季成績を一括保存（UPSERT: 同じ選手名+stat_typeは上書き）"""
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for s in stats_list:
        cursor.execute('''
            INSERT OR REPLACE INTO season_stats_2026
            (player_name, team, league, stat_type, games, plate_appearances, innings_pitched, team_games,
             batting_avg, hits, home_runs, rbi, stolen_bases, on_base_pct, slg_pct, ops,
             era, wins, losses, saves, holds, strikeouts, walks, hits_allowed, putouts, assists, errors, triples, stolen_base_caught, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            s.get('player_name'), s.get('team'), s.get('league'), s.get('stat_type'),
            s.get('games'), s.get('plate_appearances'), s.get('innings_pitched'), s.get('team_games'),
            s.get('batting_avg'), s.get('hits'), s.get('home_runs'),
            s.get('rbi'), s.get('stolen_bases'), s.get('on_base_pct'), s.get('slg_pct'), s.get('ops'),
            s.get('era'), s.get('wins'), s.get('losses'), s.get('saves'),
            s.get('holds'), s.get('strikeouts'), s.get('walks'), s.get('hits_allowed'),
            s.get('putouts'), s.get('assists'), s.get('errors'), s.get('triples'), s.get('stolen_base_caught'), now
        ))
    conn.commit()
    conn.close()

def get_all_players() -> List[Dict]:
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM players')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_season_stats(team: Optional[str] = None, stat_type: Optional[str] = None, league: Optional[str] = None) -> List[Dict]:
    """今季成績を取得。team/stat_type/leagueでフィルタ可能"""
    conn = _get_conn()
    cursor = conn.cursor()
    query = 'SELECT * FROM season_stats_2026 WHERE 1=1'
    params = []
    if team:
        query += ' AND team = ?'
        params.append(team)
    if stat_type:
        query += ' AND stat_type = ?'
        params.append(stat_type)
    if league:
        query += ' AND league = ?'
        params.append(league)
    query += ' ORDER BY games DESC'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_player_season_stats(player_name: str) -> List[Dict]:
    """特定選手の今季成績（打者・投手両方）を取得"""
    conn = _get_conn()
    cursor = conn.cursor()
    # スペースの有無を考慮した正規化（全角・半角・タブ等すべて削除）
    name_norm = re.sub(r'[\s　]', '', player_name)
    
    # SQLiteのreplaceを使用してDB側の値も正規化して比較
    cursor.execute('''
        SELECT * FROM season_stats_2026
        WHERE replace(replace(player_name, ' ', ''), '　', '') LIKE ?
        ORDER BY (CASE WHEN ops IS NOT NULL THEN 1 ELSE 0 END) DESC, games DESC
    ''', (f'%{name_norm}%',))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_stats_last_updated() -> Optional[str]:
    """成績の最終更新日時を返す"""
    conn = _get_conn()
    cursor = conn.cursor()
    row = cursor.execute('SELECT MAX(last_updated) FROM season_stats_2026').fetchone()
    conn.close()
    return row[0] if row else None

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
