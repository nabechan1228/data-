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


def _get(url: str, max_retries: int = 3) -> requests.Response:
    """指数バックオフ付きGETリクエスト（セキュリティS4）"""
    headers = {'User-Agent': random.choice(USER_AGENTS)}
    for attempt in range(max_retries):
        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.encoding = 'utf-8'
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


def scrape_batting_stats(team_code: str) -> list:
    """球団別の全打者成績をスクレイピング"""
    year = 2026
    team_name = TEAM_CODE_MAP.get(team_code, team_code)
    url = f'https://npb.jp/bis/{year}/stats/idb1_{team_code}.html'
    logger.info(f"Scraping batting stats for {team_name} from {url}")
    
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

    # 球団別ページは通常最初のテーブルが成績
    table = tables[0]
    headers = [th.text.strip() for th in table.find_all('th')]
    rows = table.find_all('tr')[1:]

    stats_list = []
    for row in rows:
        tds = row.find_all('td')
        if len(tds) < 5:
            continue
        try:
            # 選手名セル (個別ページでは「選手」または1列目)
            # ヘッダーに「選手」があるか確認
            player_idx = headers.index('選手') if '選手' in headers else 0
            player_name = tds[player_idx].text.strip()
            
            # 合計行などをスキップ
            if not player_name or player_name == 'チーム合計' or player_name == '選手':
                continue

            def col(key):
                if key in headers:
                    idx = headers.index(key)
                    return tds[idx].text.strip() if idx < len(tds) else ''
                return ''

            stats_list.append({
                'player_name': player_name,
                'team': team_name,
                'stat_type': 'batting',
                'games': _safe_int(col('試合')),
                'batting_avg': _safe_float(col('打率')),
                'hits': _safe_int(col('安打')),
                'home_runs': _safe_int(col('本塁打')),
                'rbi': _safe_int(col('打点')),
                'stolen_bases': _safe_int(col('盗塁')),
                'on_base_pct': _safe_float(col('出塁率')),
                'slg_pct': _safe_float(col('長打率')),
                'era': None,
                'wins': None,
                'losses': None,
                'saves': None,
                'holds': None,
                'strikeouts': None,
            })
        except Exception as e:
            logger.debug(f"Row parse error (batting): {e}")

    logger.info(f"  -> {len(stats_list)} batters scraped")
    return stats_list


def scrape_pitching_stats(team_code: str) -> list:
    """球団別の全投手成績をスクレイピング"""
    year = 2026
    team_name = TEAM_CODE_MAP.get(team_code, team_code)
    url = f'https://npb.jp/bis/{year}/stats/idp1_{team_code}.html'
    logger.info(f"Scraping pitching stats for {team_name} from {url}")
    
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
    headers = [th.text.strip() for th in table.find_all('th')]
    rows = table.find_all('tr')[1:]

    stats_list = []
    for row in rows:
        tds = row.find_all('td')
        if len(tds) < 5:
            continue
        try:
            player_idx = headers.index('投手') if '投手' in headers else 0
            player_name = tds[player_idx].text.strip()
            
            if not player_name or player_name == 'チーム合計' or player_name == '投手':
                continue

            def col(key):
                if key in headers:
                    idx = headers.index(key)
                    return tds[idx].text.strip() if idx < len(tds) else ''
                return ''

            stats_list.append({
                'player_name': player_name,
                'team': team_name,
                'stat_type': 'pitching',
                'games': _safe_int(col('登板')),
                'batting_avg': None,
                'hits': None,
                'home_runs': None,
                'rbi': None,
                'stolen_bases': None,
                'on_base_pct': None,
                'slg_pct': None,
                'era': _safe_float(col('防御率')),
                'wins': _safe_int(col('勝利')),
                'losses': _safe_int(col('敗北')),
                'saves': _safe_int(col('セーブ')),
                'holds': _safe_int(col('ホールド')),
                'strikeouts': _safe_int(col('三振')),
            })
        except Exception as e:
            logger.debug(f"Row parse error (pitching): {e}")

    logger.info(f"  -> {len(stats_list)} pitchers scraped")
    return stats_list


def scrape_all_stats() -> int:
    """
    全12球団の全選手成績を取得してDBに保存する。
    """
    database.ensure_stats_table()
    all_stats = []

    for team_code in TEAM_CODE_MAP.keys():
        all_stats.extend(scrape_batting_stats(team_code))
        time.sleep(0.5)
        all_stats.extend(scrape_pitching_stats(team_code))
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

