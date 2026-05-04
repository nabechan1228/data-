"""
stats_scraper.py
今季（2026年）1軍成績をNPB公式サイトから取得してDBに保存する軽量スクレイパー。
4URLを取得するだけなので全体で約10〜20秒で完了。
毎日自動実行（APScheduler経由）または手動実行可能。
"""
import requests
from bs4 import BeautifulSoup
import database
import time
import random
import logging
import re

logger = logging.getLogger(__name__)

# ランダムUser-Agent（BAN回避・セキュリティS3）
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
]

# 球団コード → 正式名マッピング
TEAM_CODE_MAP = {
    'c': '広島東洋カープ',
    'g': '読売ジャイアンツ',
    't': '阪神タイガース',
    'db': '横浜DeNAベイスターズ',
    'd': '中日ドラゴンズ',
    's': '東京ヤクルトスワローズ',
    'b': 'オリックス・バファローズ',
    'm': '千葉ロッテマリーンズ',
    'h': '福岡ソフトバンクホークス',
    'e': '東北楽天ゴールデンイーグルス',
    'l': '埼玉西武ライオンズ',
    'f': '北海道日本ハムファイターズ',
}


# リーグ分け
LEAGUE_MAP = {
    'c': 'Central', 'g': 'Central', 't': 'Central', 'db': 'Central', 'd': 'Central', 's': 'Central',
    'b': 'Pacific', 'm': 'Pacific', 'h': 'Pacific', 'e': 'Pacific', 'l': 'Pacific', 'f': 'Pacific',
}


def normalize_name(name: str) -> str:
    """名前の空白（全角・半角）および特殊記号（* + # 等）を除去して正規化する"""
    if not name: return ""
    # 先頭や途中の特殊記号を除去
    name = re.sub(r'[*+#]', '', name)
    return re.sub(r'[\s　]', '', name)


def _get(url: str, max_retries: int = 3) -> requests.Response:
    """指数バックオフ付きGETリクエスト（セキュリティS4）"""
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=headers, timeout=15)
            # 自動検出されたエンコーディングを使用（ISO-8859-1 の場合は apparent_encoding を試す）
            if res.encoding == 'ISO-8859-1':
                res.encoding = res.apparent_encoding or 'utf-8'
            
            if res.status_code == 200:
                return res
            logger.warning(f"HTTP {res.status_code} for {url}, attempt {attempt + 1}")
        except requests.RequestException as e:
            logger.warning(f"Request error for {url}: {e}, attempt {attempt + 1}")
        # 指数バックオフ: 1秒 → 2秒 → 4秒
        time.sleep(2 ** attempt)
    raise RuntimeError(f"Failed to fetch {url} after {max_retries} retries")


def _safe_float(val: str):
    try:
        # ".333" などの形式を "0.333" に補完
        v = val.strip().replace('-', '').replace('ー', '')
        if v.startswith('.'):
            v = '0' + v
        return float(v) if v else None
    except (ValueError, AttributeError):
        return None


def _safe_int(val: str):
    try:
        v = val.strip().replace('-', '').replace('ー', '')
        return int(v) if v else None
    except (ValueError, AttributeError):
        return None


def get_team_games_map() -> dict:
    """セ・パ両リーグの順位表から各球団の試合数を取得"""
    games_map = {}
    urls = [
        'https://npb.jp/bis/2026/stats/std_c.html', # セ
        'https://npb.jp/bis/2026/stats/std_p.html', # パ
    ]
    for url in urls:
        try:
            res = _get(url)
            soup = BeautifulSoup(res.text, 'html.parser')
            table = soup.find('table')
            if not table: continue
            rows = table.find_all('tr')[1:] # ヘッダー除外
            for row in rows:
                tds = row.find_all(['td', 'th'])
                if len(tds) < 2: continue
                # 順位表の形式: チーム, 試合, 勝利, 敗戦, ...
                name = tds[0].text.strip()
                games = _safe_int(tds[1].text)
                if name and games is not None:
                    # TEAM_CODE_MAP の正式名称に含まれるかチェック
                    matched = False
                    for full_name in TEAM_CODE_MAP.values():
                        if name in full_name or full_name in name:
                            games_map[full_name] = games
                            matched = True
                            break
                    if not matched:
                        games_map[name] = games
        except Exception as e:
            logger.warning(f"Failed to get team games from {url}: {e}")
    return games_map


def scrape_batting_stats(team_code: str, team_games_fallback: int = 0) -> list:
    """球団別の全打者成績をスクレイピング"""
    year = 2026
    team_name = TEAM_CODE_MAP.get(team_code, team_code)
    league = LEAGUE_MAP.get(team_code, 'Unknown')
    url = f'https://npb.jp/bis/{year}/stats/idb1_{team_code}.html'
    logger.info(f"Scraping batting stats for {team_name} ({league}) from {url}")
    
    try:
        res = _get(url)
    except Exception as e:
        logger.error(f"Failed to fetch batting stats for {team_code}: {e}")
        return []
        
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        logger.error(f"No table found at {url}")
        return []

    # 実際のデータが入っている最初のテーブルを取得
    table = tables[0]
    all_rows = table.find_all('tr')
    
    # ヘッダー行を探す（'選手'という文字列が含まれる最初のtr）
    header_row = None
    headers = []
    for row in all_rows:
        ths = row.find_all(['th', 'td'])
        txts = [th.text.strip() for th in ths]
        if '選手' in txts:
            header_row = row
            headers = txts
            break
            
    if not header_row:
        logger.error(f"Could not find header row at {url}")
        return []

    # データ行（ヘッダー行より後の行）
    rows = all_rows[all_rows.index(header_row) + 1:]

    # チーム合計行を探してチーム試合数を取得（打撃ページにはない場合が多いが念のため）
    team_games = team_games_fallback or 0
    if team_games == 0:
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells: continue
            if any('チーム合計' in c.text for c in cells):
                idx = headers.index('試合') if '試合' in headers else -1
                if idx != -1 and idx < len(cells):
                    team_games = _safe_int(cells[idx].text) or 0
                break

    stats_list = []
    max_games = 0
    parsed_rows = []
    for row in rows:
        tds = row.find_all(['td', 'th'])
        if len(tds) < 5: continue
        
        # 選手名セル
        player_idx = headers.index('選手') if '選手' in headers else 0
        player_name = tds[player_idx].text.strip()
        if not player_name or player_name in ('チーム合計', '選手', '合計'):
            continue
            
        def col_val(key):
            if key in headers:
                idx = headers.index(key)
                return tds[idx].text.strip() if idx < len(tds) else ''
            return ''
            
        g = _safe_int(col_val('試合')) or 0
        if g > max_games: max_games = g
        parsed_rows.append((row, tds, player_name))

    if team_games == 0:
        team_games = team_games_fallback or max_games
        logger.info(f"  (Fallback) Using {team_games} as team_games")

    for row, tds, player_name in parsed_rows:
        try:
            def col(key):
                if key in headers:
                    idx = headers.index(key)
                    return tds[idx].text.strip() if idx < len(tds) else ''
                return ''

            obp = _safe_float(col('出塁率'))
            slg = _safe_float(col('長打率'))
            ops = round(obp + slg, 3) if obp is not None and slg is not None else None

            stats_list.append({
                'player_name': normalize_name(player_name),
                'team': team_name,
                'league': league,
                'stat_type': 'batting',
                'games': _safe_int(col('試合')),
                'plate_appearances': _safe_int(col('打席')),
                'innings_pitched': None,
                'team_games': team_games,
                'batting_avg': _safe_float(col('打率')),
                'hits': _safe_int(col('安打')),
                'home_runs': _safe_int(col('本塁打')),
                'rbi': _safe_int(col('打点')),
                'stolen_bases': _safe_int(col('盗塁')),
                'on_base_pct': obp,
                'slg_pct': slg,
                'ops': ops,
                'era': None,
                'wins': None,
                'losses': None,
                'saves': None,
                'holds': None,
                'strikeouts': None,
                'putouts': None,
                'assists': None,
                'errors': None,
                'triples': _safe_int(col('三塁打')),
                'stolen_base_caught': _safe_int(col('盗塁刺')),
            })
        except Exception as e:
            logger.debug(f"Row parse error (batting): {e}")

    logger.info(f"  -> {len(stats_list)} batters scraped (Team Games: {team_games})")
    return stats_list


def scrape_pitching_stats(team_code: str, team_games_fallback: int = 0) -> list:
    """球団別の全投手成績をスクレイピング"""
    year = 2026
    team_name = TEAM_CODE_MAP.get(team_code, team_code)
    league = LEAGUE_MAP.get(team_code, 'Unknown')
    url = f'https://npb.jp/bis/{year}/stats/idp1_{team_code}.html'
    logger.info(f"Scraping pitching stats for {team_name} ({league}) from {url}")
    
    try:
        res = _get(url)
    except Exception as e:
        logger.error(f"Failed to fetch pitching stats for {team_code}: {e}")
        return []
        
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        logger.error(f"No table found at {url}")
        return []

    table = tables[0]
    all_rows = table.find_all('tr')
    
    # ヘッダー行を探す（'投手'または'選手'という文字列が含まれる最初のtr）
    header_row = None
    headers = []
    for row in all_rows:
        ths = row.find_all(['th', 'td'])
        txts = [th.text.strip() for th in ths]
        if '投手' in txts or '選手' in txts:
            header_row = row
            headers = txts
            break
            
    if not header_row:
        logger.error(f"Could not find header row at {url}")
        return []

    rows = all_rows[all_rows.index(header_row) + 1:]

    # チーム合計行を探してチーム試合数を取得
    team_games = team_games_fallback or 0
    if team_games == 0:
        for row in rows:
            tds = row.find_all(['td', 'th'])
            if not tds: continue
            if any(x in tds[0].text.strip() for x in ('チーム合計', '合計')):
                idx = headers.index('登板') if '登板' in headers else -1
                if idx != -1 and idx < len(tds):
                    team_games = _safe_int(tds[idx].text) or 0
                break

    stats_list = []
    max_games = 0
    parsed_rows = []
    for row in rows:
        tds = row.find_all(['td', 'th'])
        if len(tds) < 5: continue
        
        player_idx = headers.index('投手') if '投手' in headers else (headers.index('選手') if '選手' in headers else 0)
        player_name = tds[player_idx].text.strip()
        if not player_name or player_name in ('チーム合計', '投手', '合計'):
            continue
            
        def col_val(key):
            if key in headers:
                idx = headers.index(key)
                return tds[idx].text.strip() if idx < len(tds) else ''
            return ''

        g = _safe_int(col_val('登板')) or 0
        if g > max_games: max_games = g
        parsed_rows.append((row, tds, player_name))

    if team_games == 0:
        team_games = team_games_fallback or max_games
        logger.info(f"  (Fallback) Using {team_games} as team_games")

    for row, tds, player_name in parsed_rows:
        try:
            def col(key):
                if key in headers:
                    idx = headers.index(key)
                    return tds[idx].text.strip() if idx < len(tds) else ''
                return ''

            # 投球回は 123 1/3 のような形式があるため処理
            ip_str = col('投球回')
            ip_val = 0.0
            if ip_str:
                parts = ip_str.split()
                for p in parts:
                    if '/' in p:
                        f_parts = p.split('/')
                        ip_val += int(f_parts[0]) / int(f_parts[1])
                    else:
                        ip_val += float(p)

            stats_list.append({
                'player_name': normalize_name(player_name),
                'team': team_name,
                'league': league,
                'stat_type': 'pitching',
                'games': _safe_int(col('登板')),
                'plate_appearances': None,
                'innings_pitched': round(ip_val, 1),
                'team_games': team_games,
                'batting_avg': None,
                'hits': None,
                'home_runs': None,
                'rbi': None,
                'stolen_bases': None,
                'on_base_pct': None,
                'slg_pct': None,
                'ops': None,
                'era': _safe_float(col('防御率')),
                'wins': _safe_int(col('勝利')),
                'losses': _safe_int(col('敗北')),
                'saves': _safe_int(col('セーブ')),
                'holds': _safe_int(col('ホールド')),
                'strikeouts': _safe_int(col('三振')),
            })
        except Exception as e:
            logger.debug(f"Row parse error (pitching): {e}")

    logger.info(f"  -> {len(stats_list)} pitchers scraped (Team Games: {team_games})")
    return stats_list


def scrape_fielding_stats(team_code: str) -> dict:
    """球団別の全選手守備成績をスクレイピング"""
    year = 2026
    team_name = TEAM_CODE_MAP.get(team_code, team_code)
    url = f'https://npb.jp/bis/{year}/stats/idf1_{team_code}.html'
    logger.info(f"Scraping fielding stats for {team_name} from {url}")
    
    try:
        res = _get(url)
    except Exception as e:
        logger.error(f"Failed to fetch fielding stats for {team_code}: {e}")
        return {}
        
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        return {}

    fielding_data = {}
    for table in tables:
        all_rows = table.find_all('tr')
        
        header_row = None
        headers = []
        for row in all_rows:
            ths = row.find_all(['th', 'td'])
            txts = [th.text.strip() for th in ths]
            if '選手' in txts:
                header_row = row
                headers = txts
                break
        
        if not header_row:
            continue

        rows = all_rows[all_rows.index(header_row) + 1:]
        for row in rows:
            tds = row.find_all(['td', 'th'])
            if len(tds) < 5: continue
            
            player_idx = headers.index('選手') if '選手' in headers else 0
            raw_name = tds[player_idx].text.strip()
            if not raw_name or raw_name in ('チーム合計', '合計'):
                continue
                
            p_name = normalize_name(raw_name)
                
            def col(key):
                if key in headers:
                    idx = headers.index(key)
                    return tds[idx].text.strip() if idx < len(tds) else ''
                return ''

            # 同一選手が複数ポジションを守る場合があるため、合算する
            if p_name not in fielding_data:
                fielding_data[p_name] = {'putouts': 0, 'assists': 0, 'errors': 0, 'games': 0}
                
            fielding_data[p_name]['putouts'] += _safe_int(col('刺殺')) or 0
            fielding_data[p_name]['assists'] += _safe_int(col('補殺')) or 0
            fielding_data[p_name]['errors'] += _safe_int(col('失策')) or 0
            fielding_data[p_name]['games'] = max(fielding_data[p_name]['games'], _safe_int(col('試合')) or 0)

    return fielding_data


def scrape_all_stats() -> int:
    """
    全12球団の全選手成績を取得してDBに保存する。
    """
    database.ensure_stats_table()
    all_stats = []

    # 最初に正確な試合数を取得
    team_games_map = get_team_games_map()
    logger.info(f"Team games map: {team_games_map}")

    for team_code in TEAM_CODE_MAP.keys():
        team_name = TEAM_CODE_MAP.get(team_code)
        fallback_games = team_games_map.get(team_name, 0)
        
        # 打撃成績取得
        batters = scrape_batting_stats(team_code, fallback_games)
        # 守備成績取得
        fielding = scrape_fielding_stats(team_code)
        
        # 打撃成績に守備データをマージ
        for b in batters:
            f = fielding.get(normalize_name(b['player_name']))
            if f:
                b['putouts'] = f['putouts']
                b['assists'] = f['assists']
                b['errors'] = f['errors']
                # 守備試合数の方が正確な場合があるが、一旦打撃試合数優先
        
        all_stats.extend(batters)
        time.sleep(0.5)
        
        # 投手成績取得
        pitchers = scrape_pitching_stats(team_code, fallback_games)
        # 投手にも守備データをマージ（投手の守備成績もidf1に含まれる）
        for p in pitchers:
            f = fielding.get(normalize_name(p['player_name']))
            if f:
                p['putouts'] = f['putouts']
                p['assists'] = f['assists']
                p['errors'] = f['errors']
                
        all_stats.extend(pitchers)
        time.sleep(0.5)

    database.save_season_stats(all_stats)
    logger.info(f"Season stats update complete: {len(all_stats)} records saved.")
    return len(all_stats)


if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    sys.stdout.reconfigure(encoding='utf-8')
    count = scrape_all_stats()
    print(f"Done. {count} records saved.")
