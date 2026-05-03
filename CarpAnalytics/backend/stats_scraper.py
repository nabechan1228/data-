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

# 球団略称 → 正式名マッピング（NPBサイトの括弧内の略称から変換）
TEAM_ABBR_MAP = {
    '広': '広島東洋カープ',
    '巨': '読売ジャイアンツ',
    '神': '阪神タイガース',
    'デ': '横浜DeNAベイスターズ',
    'ヤ': '東京ヤクルトスワローズ',
    '中': '中日ドラゴンズ',
    'オ': 'オリックス・バファローズ',
    'ロ': '千葉ロッテマリーンズ',
    'ソ': '福岡ソフトバンクホークス',
    '楽': '東北楽天ゴールデンイーグルス',
    '西': '埼玉西武ライオンズ',
    '日': '北海道日本ハムファイターズ',
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


def _parse_player_name_and_team(cell_text: str):
    """
    '佐藤　輝明(神)' のような形式から選手名と球団を分離する。
    """
    import re
    match = re.match(r'(.+?)\((.)\)', cell_text.strip())
    if match:
        name = match.group(1).strip()
        abbr = match.group(2).strip()
        team = TEAM_ABBR_MAP.get(abbr, abbr)
        return name, team
    return cell_text.strip(), ''


def _safe_float(val: str):
    try:
        v = val.strip().replace('-', '').replace('ー', '')
        return float(v) if v else None
    except (ValueError, AttributeError):
        return None


def _safe_int(val: str):
    try:
        v = val.strip().replace('-', '').replace('ー', '')
        return int(v) if v else None
    except (ValueError, AttributeError):
        return None


def scrape_batting_stats(league: str) -> list:
    """打者成績をスクレイピング。league='c' or 'p'"""
    year = 2026
    url = f'https://npb.jp/bis/{year}/stats/bat_{league}.html'
    logger.info(f"Scraping batting stats from {url}")
    res = _get(url)
    soup = BeautifulSoup(res.text, 'html.parser')

    tables = soup.find_all('table')
    if not tables:
        logger.error(f"No table found at {url}")
        return []

    table = tables[0]
    headers = [th.text.strip() for th in table.find_all('th')]
    rows = table.find_all('tr')[1:]  # ヘッダー行をスキップ

    stats_list = []
    for row in rows:
        tds = row.find_all('td')
        if len(tds) < 5:
            continue
        try:
            # 選手名セルを取得（リンク内のテキスト）
            name_td = tds[1]
            raw_name = name_td.text.strip()
            player_name, team = _parse_player_name_and_team(raw_name)

            def col(key):
                if key in headers:
                    idx = headers.index(key)
                    return tds[idx].text.strip() if idx < len(tds) else ''
                return ''

            stats_list.append({
                'player_name': player_name,
                'team': team,
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
            logger.warning(f"Error parsing batting row: {e}")

    logger.info(f"  -> {len(stats_list)} batters scraped")
    return stats_list


def scrape_pitching_stats(league: str) -> list:
    """投手成績をスクレイピング。league='c' or 'p'"""
    year = 2026
    url = f'https://npb.jp/bis/{year}/stats/pit_{league}.html'
    logger.info(f"Scraping pitching stats from {url}")
    res = _get(url)
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
            name_td = tds[1]
            raw_name = name_td.text.strip()
            player_name, team = _parse_player_name_and_team(raw_name)

            def col(key):
                if key in headers:
                    idx = headers.index(key)
                    return tds[idx].text.strip() if idx < len(tds) else ''
                return ''

            stats_list.append({
                'player_name': player_name,
                'team': team,
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
            logger.warning(f"Error parsing pitching row: {e}")

    logger.info(f"  -> {len(stats_list)} pitchers scraped")
    return stats_list


def scrape_all_stats() -> int:
    """
    セ・パ両リーグの打者・投手成績を取得してDBに保存する。
    戻り値: 保存したレコード数
    """
    database.ensure_stats_table()
    all_stats = []

    for league in ['c', 'p']:
        all_stats.extend(scrape_batting_stats(league))
        time.sleep(0.5)
        all_stats.extend(scrape_pitching_stats(league))
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
