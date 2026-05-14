import sqlite3
from typing import List, Dict, Optional
import os
import re
from datetime import datetime

# 絶対パスでDBを指定（ディレクトリトラバーサル対策）
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(_BASE_DIR, "carp_data.db")

# ─────────────────────────────────────
# テーブル定義 (シングルソース・オブ・トゥルース)
# ─────────────────────────────────────
_PLAYERS_DDL = '''
    CREATE TABLE IF NOT EXISTS players (
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
        pot_axes_upper_json TEXT,
        pot_axes_lower_json TEXT,
        fielding_json TEXT,
        farm_stats_json TEXT,
        is_awakened BOOLEAN,
        image_url TEXT,
        similarity_name TEXT,
        similarity_score REAL,
        style_tag TEXT,
        is_breaking_out BOOLEAN,
        ghost_axes_json TEXT
    )
'''

_SEASON_STATS_DDL = '''
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
        walks             INTEGER,
        hits_allowed      INTEGER,
        putouts           INTEGER,
        assists           INTEGER,
        errors            INTEGER,
        triples           INTEGER,
        stolen_base_caught INTEGER,
        last_updated      TEXT,
        UNIQUE(player_name, stat_type) ON CONFLICT REPLACE
    )
'''

_SNAPSHOTS_DDL = '''
    CREATE TABLE IF NOT EXISTS player_daily_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        player_name TEXT NOT NULL,
        team TEXT,
        ops REAL,
        k9 REAL,
        similarity_name TEXT,
        similarity_score REAL,
        is_breaking_out BOOLEAN,
        UNIQUE(snapshot_date, player_name) ON CONFLICT REPLACE
    )
'''

# S-1: 許可するカラム名のホワイトリスト（動的DDLのインジェクション対策）
_ALLOWED_MIGRATION_COLUMNS: List[tuple] = [
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
    ("hits_allowed", "INTEGER"),
]


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ping_db() -> None:
    """DB が読み取り可能か検証。失敗時は例外を送出。"""
    with _get_conn() as conn:
        conn.execute("SELECT 1").fetchone()


def _like_escape_metachars(s: str) -> str:
    """LIKE パターン内で % _ \\ をリテラルとして扱うためのエスケープ（ESCAPE '\\\\' 用）。"""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _like_substring_pattern(normalized_name: str) -> str:
    return f"%{_like_escape_metachars(normalized_name)}%"


def init_db():
    """DBを初期化（全テーブルを再作成）"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DROP TABLE IF EXISTS players')
        cursor.execute('DROP TABLE IF EXISTS season_stats_2026')
        cursor.execute('DROP TABLE IF EXISTS player_daily_snapshots')
        # IF NOT EXISTS を除いたバージョンで再作成
        cursor.execute(_PLAYERS_DDL.replace('IF NOT EXISTS ', ''))
        cursor.execute(_SEASON_STATS_DDL)
        cursor.execute(_SNAPSHOTS_DDL)
        conn.commit()


def ensure_stats_table():
    """season_stats_2026テーブルを作成し、不足カラムを追加（マイグレーション）"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(_SEASON_STATS_DDL)
        cursor.execute(_SNAPSHOTS_DDL)

        # 既存テーブルへのカラム追加（S-1: ホワイトリストのみ許可）
        cursor.execute("PRAGMA table_info(season_stats_2026)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        for col_name, col_type in _ALLOWED_MIGRATION_COLUMNS:
            # ホワイトリスト内の識別子のみ使用（外部入力なし）
            if col_name not in existing_columns:
                # col_name/col_type はリテラル定数のみ。f-stringだがインジェクションリスクなし
                cursor.execute(f"ALTER TABLE season_stats_2026 ADD COLUMN {col_name} {col_type}")
                print(f"Added column {col_name} to season_stats_2026")

        conn.commit()


def save_players(players_data: List[Dict]):
    """全選手データを一括保存（既存データを全削除して置換）"""
    # S-4: with文でコネクションリークを防止
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM players')
        for p in players_data:
            cursor.execute('''
                INSERT INTO players (
                    team, name, position, age, years_in_pro, current_performance, potential_score,
                    batting_avg, home_runs, era, defense, speed, putouts, assists, errors, triples,
                    stolen_base_caught, perf_area, pot_area, convergence_rate, is_unbalanced,
                    perf_axes_json, pot_axes_json, pot_axes_upper_json, pot_axes_lower_json,
                    fielding_json, farm_stats_json, is_awakened, image_url,
                    similarity_name, similarity_score, style_tag, is_breaking_out, ghost_axes_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                p.get('team'), p.get('name'), p.get('position'), p.get('age'), p.get('years_in_pro'),
                p.get('current_performance'), p.get('potential_score'),
                p.get('batting_avg'), p.get('home_runs'), p.get('era'),
                p.get('defense'), p.get('speed'), p.get('putouts'), p.get('assists'),
                p.get('errors'), p.get('triples'), p.get('stolen_base_caught'),
                p.get('perf_area'), p.get('pot_area'), p.get('convergence_rate'), p.get('is_unbalanced'),
                p.get('perf_axes_json'), p.get('pot_axes_json'), p.get('pot_axes_upper_json'),
                p.get('pot_axes_lower_json'), p.get('fielding_json'), p.get('farm_stats_json'),
                p.get('is_awakened'), p.get('image_url'),
                p.get('similarity_name'), p.get('similarity_score'),
                p.get('style_tag'), p.get('is_breaking_out'), p.get('ghost_axes_json')
            ))
        conn.commit()


def save_season_stats(stats_list: List[Dict]):
    """今季成績を一括保存（UPSERT: 同じ選手名+stat_typeは上書き）"""
    now = datetime.now().isoformat()
    # S-4: with文でコネクションリークを防止
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for s in stats_list:
            cursor.execute('''
                INSERT OR REPLACE INTO season_stats_2026
                (player_name, team, league, stat_type, games, plate_appearances, innings_pitched,
                 team_games, batting_avg, hits, home_runs, rbi, stolen_bases, on_base_pct,
                 slg_pct, ops, era, wins, losses, saves, holds, strikeouts, walks, hits_allowed,
                 putouts, assists, errors, triples, stolen_base_caught, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                s.get('player_name'), s.get('team'), s.get('league'), s.get('stat_type'),
                s.get('games'), s.get('plate_appearances'), s.get('innings_pitched'),
                s.get('team_games'), s.get('batting_avg'), s.get('hits'), s.get('home_runs'),
                s.get('rbi'), s.get('stolen_bases'), s.get('on_base_pct'), s.get('slg_pct'),
                s.get('ops'), s.get('era'), s.get('wins'), s.get('losses'), s.get('saves'),
                s.get('holds'), s.get('strikeouts'), s.get('walks'), s.get('hits_allowed'),
                s.get('putouts'), s.get('assists'), s.get('errors'), s.get('triples'),
                s.get('stolen_base_caught'), now
            ))
        conn.commit()


def get_all_players() -> List[Dict]:
    with _get_conn() as conn:
        rows = conn.execute('SELECT * FROM players').fetchall()
    return [dict(row) for row in rows]


def get_player_by_id(player_id: int) -> Optional[Dict]:
    with _get_conn() as conn:
        row = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()
    return dict(row) if row else None


def get_season_stats(
    team: Optional[str] = None,
    stat_type: Optional[str] = None,
    league: Optional[str] = None,
) -> List[Dict]:
    """今季成績を取得。team/stat_type/leagueでフィルタ可能"""
    # パラメータ化クエリで SQLインジェクション対策済み
    query = 'SELECT * FROM season_stats_2026 WHERE 1=1'
    params: List = []
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

    with _get_conn() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_player_season_stats(player_name: str) -> List[Dict]:
    """特定選手の今季成績（打者・投手両方）を取得。完全一致優先、部分一致フォールバック"""
    # スペースの有無を考慮した正規化
    name_norm = re.sub(r'[\s　]', '', player_name)

    with _get_conn() as conn:
        # M-2: 完全一致を優先（意図しない別選手へのマッチを防ぐ）
        rows = conn.execute('''
            SELECT * FROM season_stats_2026
            WHERE replace(replace(player_name, ' ', ''), '　', '') = ?
            ORDER BY (CASE WHEN ops IS NOT NULL THEN 1 ELSE 0 END) DESC, games DESC
        ''', (name_norm,)).fetchall()

        # 完全一致がなければ部分一致（フォールバック）。LIKE メタ文字は ESCAPE で無効化
        if not rows:
            like_pat = _like_substring_pattern(name_norm)
            rows = conn.execute('''
                SELECT * FROM season_stats_2026
                WHERE replace(replace(player_name, ' ', ''), '　', '') LIKE ? ESCAPE '\\'
                ORDER BY (CASE WHEN ops IS NOT NULL THEN 1 ELSE 0 END) DESC, games DESC
            ''', (like_pat,)).fetchall()

    return [dict(row) for row in rows]


def get_stats_last_updated() -> Optional[str]:
    """成績の最終更新日時を返す"""
    with _get_conn() as conn:
        row = conn.execute('SELECT MAX(last_updated) FROM season_stats_2026').fetchone()
    return row[0] if row else None


def save_daily_snapshots(snapshots: List[Dict]):
    """毎日のスナップショットを保存"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        for s in snapshots:
            cursor.execute('''
                INSERT OR REPLACE INTO player_daily_snapshots
                (snapshot_date, player_name, team, ops, k9, similarity_name, similarity_score, is_breaking_out)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                s.get('snapshot_date'), s.get('player_name'), s.get('team'),
                s.get('ops'), s.get('k9'), s.get('similarity_name'),
                s.get('similarity_score'), s.get('is_breaking_out')
            ))
        conn.commit()


def get_player_snapshots(player_name: str, days: int = 30) -> List[Dict]:
    """特定選手の直近N日間のスナップショットを取得"""
    name_norm = re.sub(r'[\s　]', '', player_name)
    like_pat = _like_substring_pattern(name_norm)
    with _get_conn() as conn:
        rows = conn.execute('''
            SELECT * FROM player_daily_snapshots
            WHERE replace(replace(player_name, ' ', ''), '　', '') LIKE ? ESCAPE '\\'
            ORDER BY snapshot_date DESC
            LIMIT ?
        ''', (like_pat, days)).fetchall()
    return [dict(row) for row in rows]


def update_player_breaking_out(player_name: str, is_breaking_out: bool):
    """覚醒フラグの直接更新"""
    name_norm = re.sub(r'[\s　]', '', player_name)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            UPDATE players SET is_breaking_out = ?
            WHERE replace(replace(name, ' ', ''), '　', '') = ?
        ''', (is_breaking_out, name_norm))
        conn.commit()


if __name__ == "__main__":
    init_db()
    print("Database initialized.")
