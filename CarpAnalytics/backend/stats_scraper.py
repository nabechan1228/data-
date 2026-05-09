"""
stats_scraper.py
今季NPB1軍成績をNPB公式サイトから取得してDBに保存する軽量スクレイパー。
"""
import requests
from bs4 import BeautifulSoup
import database
import time
import random
import logging
import re

# R-3: 現在シーズン年をモジュール定数に集約（マジックナンバー排除）
CURRENT_YEAR = 2026

logger = logging.getLogger(__name__)

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
]

TEAM_CODE_MAP = {
    'c': '広島東洋カープ', 'g': '読売ジャイアンツ', 't': '阪神タイガース', 'db': '横浜DeNAベイスターズ',
    'd': '中日ドラゴンズ', 's': '東京ヤクルトスワローズ', 'b': 'オリックス・バファローズ',
    'm': '千葉ロッテマリーンズ', 'h': '福岡ソフトバンクホークス', 'e': '東北楽天ゴールデンイーグルス',
    'l': '埼玉西武ライオンズ', 'f': '北海道日本ハムファイターズ',
}

LEAGUE_MAP = {
    'c': 'Central', 'g': 'Central', 't': 'Central', 'db': 'Central', 'd': 'Central', 's': 'Central',
    'b': 'Pacific', 'm': 'Pacific', 'h': 'Pacific', 'e': 'Pacific', 'l': 'Pacific', 'f': 'Pacific',
}

def normalize_name(name: str) -> str:
    if not name: return ""
    name = re.sub(r'[*+#]', '', name)
    return re.sub(r'[\s　]', '', name)

def _get(url: str, max_retries: int = 3) -> requests.Response:
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                # 明示的にShift_JIS（cp932）を指定する場合が多いNPBへの対応
                content_sample = res.content[:4096].lower()
                if b'charset=utf-8' in content_sample or b'charset="utf-8"' in content_sample:
                    res.encoding = 'utf-8'
                elif b'shift_jis' in content_sample or b'cp932' in content_sample or b'ms932' in content_sample:
                    res.encoding = 'cp932'
                else:
                    # requestsの推測を使用
                    res.encoding = res.apparent_encoding
                    if res.encoding == 'ISO-8859-1': # 誤判定の定番
                        res.encoding = 'cp932'
                return res
            logger.warning(f"HTTP {res.status_code} for {url}, attempt {attempt + 1}")
        except requests.RequestException as e:
            logger.warning(f"Request error for {url}: {e}, attempt {attempt + 1}")
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {url} after {max_retries} retries")

def _safe_float(val: str):
    try:
        v = val.strip().replace('-', '').replace('ー', '')
        if v.startswith('.'): v = '0' + v
        return float(v) if v else None
    except (ValueError, AttributeError): return None

def _safe_int(val: str):
    try:
        v = val.strip().replace('-', '').replace('ー', '')
        return int(v) if v else None
    except (ValueError, AttributeError): return None

def get_team_games_map() -> dict:
    games_map = {}
    urls = [
        f'https://npb.jp/bis/{CURRENT_YEAR}/stats/std_c.html',
        f'https://npb.jp/bis/{CURRENT_YEAR}/stats/std_p.html',
    ]
    for url in urls:
        try:
            res = _get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table')
            if not table: continue
            rows = table.find_all('tr')[1:]
            for row in rows:
                tds = row.find_all(['td', 'th'])
                if len(tds) < 2: continue
                name = tds[0].text.strip()
                games = _safe_int(tds[1].text)
                if name and games is not None:
                    for full_name in TEAM_CODE_MAP.values():
                        if name in full_name or full_name in name:
                            games_map[full_name] = games
                            break
        except Exception as e:
            logger.warning(f"Failed to get team games from {url}: {e}")
    return games_map

def scrape_batting_stats(team_code: str, team_games_fallback: int = 0) -> list:
    year = CURRENT_YEAR
    team_name = TEAM_CODE_MAP.get(team_code, team_code)
    league = LEAGUE_MAP.get(team_code, 'Unknown')
    url = f'https://npb.jp/bis/{year}/stats/idb1_{team_code}.html'
    res = _get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    if not tables: return []
    table = tables[0]
    all_rows = table.find_all('tr')
    header_row = next((r for r in all_rows if '選手' in r.text), None)
    if not header_row: return []
    headers = [th.text.strip() for th in header_row.find_all(['th', 'td'])]
    rows = all_rows[all_rows.index(header_row) + 1:]
    stats_list = []
    for row in rows:
        tds = row.find_all(['td', 'th'])
        if len(tds) < 5: continue
        p_name = tds[headers.index('選手')].text.strip()
        if not p_name or p_name in ('チーム合計', '選手', '合計'): continue
        def col(key):
            idx = headers.index(key) if key in headers else -1
            return tds[idx].text.strip() if idx != -1 and idx < len(tds) else ''
        obp = _safe_float(col('出塁率'))
        slg = _safe_float(col('長打率'))
        stats_list.append({
            'player_name': normalize_name(p_name),
            'team': team_name, 'league': league, 'stat_type': 'batting',
            'games': _safe_int(col('試合')), 'plate_appearances': _safe_int(col('打席')),
            'batting_avg': _safe_float(col('打率')), 'hits': _safe_int(col('安打')), 'home_runs': _safe_int(col('本塁打')),
            'rbi': _safe_int(col('打点')), 'stolen_bases': _safe_int(col('盗塁')),
            'on_base_pct': obp, 'slg_pct': slg, 'ops': round(obp + slg, 3) if obp and slg else None,
            'triples': _safe_int(col('三塁打')), 'stolen_base_caught': _safe_int(col('盗塁刺')),
            'team_games': team_games_fallback
        })
    return stats_list

def scrape_pitching_stats(team_code: str, team_games_fallback: int = 0) -> list:
    year = CURRENT_YEAR
    team_name = TEAM_CODE_MAP.get(team_code, team_code)
    league = LEAGUE_MAP.get(team_code, 'Unknown')
    url = f'https://npb.jp/bis/{year}/stats/idp1_{team_code}.html'
    res = _get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    if not tables: return []
    table = tables[0]
    all_rows = table.find_all('tr')
    header_row = next((r for r in all_rows if any(x in r.text for x in ('投手', '選手'))), None)
    if not header_row: return []
    headers = [th.text.strip() for th in header_row.find_all(['th', 'td'])]
    rows = all_rows[all_rows.index(header_row) + 1:]
    stats_list = []
    for row in rows:
        tds = row.find_all(['td', 'th'])
        if len(tds) < 5: continue
        p_name = tds[next(i for i, h in enumerate(headers) if h in ('投手', '選手'))].text.strip()
        if not p_name or p_name in ('チーム合計', '投手', '合計'): continue
        def col(key):
            idx = headers.index(key) if key in headers else -1
            return tds[idx].text.strip() if idx != -1 and idx < len(tds) else ''
        ip_str = col('投球回')
        ip_val = sum(float(p.split('/')[0])/int(p.split('/')[1]) if '/' in p else float(p) for p in ip_str.split()) if ip_str else 0.0
        stats_list.append({
            'player_name': normalize_name(p_name), 'team': team_name, 'league': league, 'stat_type': 'pitching',
            'games': _safe_int(col('登板')), 'innings_pitched': round(ip_val, 1),
            'era': _safe_float(col('防御率')), 'wins': _safe_int(col('勝利')), 'losses': _safe_int(col('敗北')),
            'saves': _safe_int(col('セーブ')), 'holds': _safe_int(col('ホールド')), 'strikeouts': _safe_int(col('三振')),
            'walks': _safe_int(col('四球')), 'hits_allowed': _safe_int(col('被安打')),
            'team_games': team_games_fallback
        })
    return stats_list

def scrape_fielding_stats(team_code: str) -> dict:
    year = CURRENT_YEAR
    url = f'https://npb.jp/bis/{year}/stats/idf1_{team_code}.html'
    res = _get(url)
    soup = BeautifulSoup(res.text, 'html.parser')
    fielding_data = {}
    
    current_pos = "Unknown"
    for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'caption', 'table', 'div', 'th']):
        if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'caption', 'th'] or 'stats_title' in elem.get('class', []) or 'stitle' in elem.get('class', []):
            text = elem.text.strip()
            for p in ["投手", "捕手", "一塁手", "二塁手", "三塁手", "遊撃手", "外野手"]:
                if p in text and len(text) < 15:
                    current_pos = p
                    break
            if elem.name != 'table':
                continue

        if elem.name == 'table':
            pos_key = current_pos
            all_rows = elem.find_all('tr')
            
            header_row = None
            for r in all_rows:
                if any(k in r.text for k in ['選手', '守備率', '刺殺']):
                    header_row = r
                    break
            
            if not header_row: continue
            cols = header_row.find_all(['th', 'td'])
            headers = [c.text.strip() for c in cols]
            rows = all_rows[all_rows.index(header_row) + 1:]
            
            for row in rows:
                tds = row.find_all(['td', 'th'])
                if len(tds) < 5: continue
                try:
                    raw_name = tds[headers.index('選手')].text.strip()
                    if not raw_name or raw_name in ('チーム合計', '合計'): continue
                    p_name = normalize_name(raw_name)
                    
                    if p_name not in fielding_data:
                        fielding_data[p_name] = {'positions': {}}
                    
                    def col(key):
                        idx = headers.index(key) if key in headers else -1
                        return tds[idx].text.strip() if idx != -1 and idx < len(tds) else ''
                    
                    fielding_data[p_name]['positions'][pos_key] = {
                        'putouts': _safe_int(col('刺殺')) or 0,
                        'assists': _safe_int(col('補殺')) or 0,
                        'errors': _safe_int(col('失策')) or 0,
                        'games': _safe_int(col('試合')) or 0
                    }
                except Exception as e:
                    logger.warning(f'Failed to parse fielding row for {pos}: {e}')
                    continue
    return fielding_data

def scrape_farm_stats(team_code: str) -> dict:
    year = CURRENT_YEAR
    url = f'https://npb.jp/bis/{year}/stats/idb2_{team_code}.html'
    try:
        res = _get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        table = soup.find('table')
        if not table: return {}
        all_rows = table.find_all('tr')
        header_row = next((r for r in all_rows if '選手' in r.text), None)
        if not header_row: return {}
        headers = [th.text.strip() for th in header_row.find_all(['th', 'td'])]
        rows = all_rows[all_rows.index(header_row) + 1:]
        farm_data = {}
        for row in rows:
            tds = row.find_all(['td', 'th'])
            if len(tds) < 5: continue
            p_name = normalize_name(tds[headers.index('選手')].text.strip())
            if not p_name or p_name in ('チーム合計', '合計'): continue
            def col(key):
                idx = headers.index(key) if key in headers else -1
                return tds[idx].text.strip() if idx != -1 and idx < len(tds) else ''
            obp = _safe_float(col('出塁率')) or 0
            slg = _safe_float(col('長打率')) or 0
            farm_data[p_name] = {
                'avg': _safe_float(col('打率')), 'hr': _safe_int(col('本塁打')),
                'games': _safe_int(col('試合')), 'ops': round(obp + slg, 3)
            }
        return farm_data
    except Exception as e:
        logger.warning(f'Failed to scrape farm stats for team {team_code}: {e}')
        return {}

def scrape_all_stats() -> int:
    database.ensure_stats_table()
    all_stats = []
    team_games_map = get_team_games_map()
    for team_code in TEAM_CODE_MAP.keys():
        team_name = TEAM_CODE_MAP.get(team_code)
        fallback_games = team_games_map.get(team_name, 0)
        batters = scrape_batting_stats(team_code, fallback_games)
        fielding = scrape_fielding_stats(team_code)
        
        for b in batters:
            f = fielding.get(normalize_name(b['player_name']))
            if f and 'positions' in f:
                b['putouts'] = sum(p.get('putouts', 0) for p in f['positions'].values())
                b['assists'] = sum(p.get('assists', 0) for p in f['positions'].values())
                b['errors'] = sum(p.get('errors', 0) for p in f['positions'].values())
            else:
                b['putouts'], b['assists'], b['errors'] = 0, 0, 0
        all_stats.extend(batters)
        
        time.sleep(0.5)
        
        pitchers = scrape_pitching_stats(team_code, fallback_games)
        for p in pitchers:
            f = fielding.get(normalize_name(p['player_name']))
            if f and 'positions' in f:
                p['putouts'] = sum(p_data.get('putouts', 0) for p_data in f['positions'].values())
                p['assists'] = sum(p_data.get('assists', 0) for p_data in f['positions'].values())
                p['errors'] = sum(p_data.get('errors', 0) for p_data in f['positions'].values())
            else:
                p['putouts'], p['assists'], p['errors'] = 0, 0, 0
        all_stats.extend(pitchers)
        time.sleep(0.5)
    database.save_season_stats(all_stats)
    return len(all_stats)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    scrape_all_stats()
