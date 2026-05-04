import requests
from bs4 import BeautifulSoup
import database
import potential_engine
import stats_scraper
import time
import json
import logging
import random
import os
import re
from datetime import date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DRAFT_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'draft_cache.json')

def load_draft_cache():
    if os.path.exists(DRAFT_CACHE_FILE):
        try:
            with open(DRAFT_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_draft_cache(cache):
    with open(DRAFT_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def get_draft_year(player_name, player_id, session, cache):
    if not player_id: return None
    if player_id in cache:
        return cache[player_id]
        
    logger.info(f'Fetching detail for {player_name} ({player_id})...')
    url = f'https://npb.jp/bis/players/{player_id}.html'
    try:
        res = stats_scraper._get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. Look for Draft info
        draft_label = '\u30c9\u30e9\u30d5\u30c8'
        th = soup.find('th', string=draft_label)
        if not th:
             th = soup.find('th', string=lambda s: s and draft_label in s)
        
        if th:
            td = th.find_next_sibling('td')
            match = re.search(r'(\d{4})', td.text)
            if match:
                year = int(match.group(1))
                cache[player_id] = year
                return year
                
        # 2. Look for first year in stats table
        first_year_td = soup.select_one('.registerStats .year')
        if first_year_td:
            try:
                year = int(first_year_td.text.strip())
                cache[player_id] = year - 1
                return year - 1
            except:
                pass
    except Exception as e:
        logger.error(f'Error fetching detail for {player_id}: {e}')
        
    return None

def scrape_real_data(target_team_code=None):
    database.init_db()
    
    team_codes = [target_team_code] if target_team_code else stats_scraper.TEAM_CODE_MAP.keys()
    
    all_players_collected = []
    draft_cache = load_draft_cache()
    session = requests.Session()
    
    for team_code in team_codes:
        team_name = stats_scraper.TEAM_CODE_MAP.get(team_code)
        logger.info(f'Scraping {team_name}...')
        
        url = f'https://npb.jp/bis/teams/rst_{team_code}.html'
        res = stats_scraper._get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        fielding = stats_scraper.scrape_fielding_stats(team_code)
        farm_stats = stats_scraper.scrape_farm_stats(team_code)
        
        rows = soup.find_all('tr')
        current_pos_category = ''
        team_players = []
        
        for row in rows:
            if 'rosterMainHead' in row.get('class', []):
                th_pos = row.find('th', class_='rosterPos')
                if th_pos:
                    current_pos_category = th_pos.text.strip()
                continue
            
            if 'rosterPlayer' not in row.get('class', []):
                continue
            
            if any(x in current_pos_category for x in ['\u76e3\u7763', '\u30b3\u30fc\u30c1']):
                continue

            tds = row.find_all('td')
            if len(tds) < 3: continue
            
            name_raw = tds[1].text.strip()
            player_name = stats_scraper.normalize_name(name_raw)
            pos = current_pos_category
            
            a_tag = tds[1].find('a')
            player_id = ''
            if a_tag:
                player_id = a_tag['href'].split('/')[-1].replace('.html', '')

            birth_str = tds[2].text.strip()
            age = 25
            years = 5
            today = date(2026, 5, 4)
            if birth_str and '.' in birth_str:
                try:
                    parts = birth_str.split('.')
                    birth_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
                    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                except Exception as e:
                    logger.error(f'Error calculating age for {player_name}: {e}')

            draft_year = get_draft_year(player_name, player_id, session, draft_cache)
            if draft_year:
                years = 2026 - draft_year
            else:
                if age <= 22:
                    years = max(1, age - 18 + 1)
                else:
                    years = max(1, age - 22 + 1)

            stats = database.get_player_season_stats(player_name)
            batting = next((s for s in stats if s['stat_type'] == 'batting'), None)
            pitching = next((s for s in stats if s['stat_type'] == 'pitching'), None)
            
            batting_avg = batting['batting_avg'] if batting else None
            home_runs = batting['home_runs'] if batting else None
            era = pitching['era'] if pitching else None
            
            p_farm = farm_stats.get(player_name, {})
            f_data = fielding.get(player_name, {})
            f_positions = f_data.get('positions', {})
            
            current_perf = potential_engine.calculate_current_performance(
                batting_avg=batting_avg,
                home_runs=home_runs,
                era=era,
                positions_data=f_positions,
                farm_stats=p_farm,
                speed=50 
            )
            
            pot_score = potential_engine.calculate_potential_score(
                age=age, years_in_pro=years, current_performance=current_perf
            )
            
            if not era:
                m_avg = batting_avg if batting_avg is not None else (p_farm.get('avg', 0) * 0.8)
                m_hr = home_runs if home_runs is not None else (p_farm.get('hr', 0) * 0.7)
                m_slg = (batting['slg_pct'] if batting else None) or (p_farm.get('ops', 0) * 0.6)
                
                power_score = 50
                if m_slg:
                    power_score = (m_slg - 0.300) * 150 + 50
                if m_hr:
                    power_score += m_hr * 2
                
                meet_score = 50
                if m_avg:
                    meet_score = (m_avg - 0.200) * 250 + 40

                perf_axes = [
                    max(10, min(100, power_score)), 
                    max(10, min(100, meet_score)),  
                    min(100, 50 + (p_farm.get('games', 0) / 10)), 
                    potential_engine.calculate_subscores(f_positions)['defense'],
                    current_perf
                ]
                sim_name, sim_score, ghost_axes, style_tag = potential_engine.find_best_role_model(perf_axes, is_pitcher=False)
            else:
                ip = pitching['innings_pitched'] if pitching else 0
                so = pitching['strikeouts'] if pitching else 0
                bb = pitching['walks'] if pitching else 0
                gs = pitching['games'] if pitching else 1
                
                k9 = (so * 9 / ip) if ip > 0 else 5.0
                bb9 = (bb * 9 / ip) if ip > 0 else 3.5
                
                stuff = (k9 - 4.0) * 12 + 40
                control = 100 - (bb9 * 12)
                stamina = (ip / gs) * 15 + 10 if gs > 0 else 30
                breaking = (stuff + control) / 2 + random.uniform(-5, 5)
                
                perf_axes = [
                    max(10, min(100, stuff)),    
                    max(10, min(100, control)),  
                    max(10, min(100, stamina)),  
                    max(10, min(100, breaking)), 
                    current_perf
                ]
                sim_name, sim_score, ghost_axes, style_tag = potential_engine.find_best_role_model(perf_axes, is_pitcher=True)
            
            perf_axes = [max(10, min(100, x + random.uniform(-1, 1))) for x in perf_axes]
            pot_axes = [max(10, min(100, pot_score)) for _ in range(5)] # 歪みを修正
            
            perf_area = potential_engine.calculate_chart_area(perf_axes)
            pot_area = potential_engine.calculate_chart_area(pot_axes)
            
            # 一芸特化（Unbalanced）の判定: 最大値と最小値の差が40以上
            is_unbalanced = (max(perf_axes) - min(perf_axes)) > 40

            # 勝負強さ（Clutch）の判定: 打点(RBI)が本塁打数に対して高いか
            rbi = batting['rbi'] if batting else 0
            is_clutch = False
            if not era and batting:
                expected_rbi = (home_runs or 0) * 1.5 + 5
                if rbi > expected_rbi and rbi > 10:
                    is_clutch = True
            elif era:
                # 投手の場合は防御率が良く、かつ勝利数が多い場合など（簡易判定）
                wins = pitching['wins'] if pitching else 0
                if era < 3.0 and wins > 3:
                    is_clutch = True

            # 覚醒判定: 収束率が高い or 勝負強さがある
            convergence = (perf_area / pot_area) if pot_area > 0 else 0
            is_awakened = convergence > 0.82 or is_clutch

            # ブレイクアウト（覚醒の兆し）判定: 若手かつ収束率が一定以上、または未完の大器
            is_breaking_out = False
            if age <= 25:
                if 0.65 < convergence <= 0.82: # 収束に向かっている若手
                    is_breaking_out = True
                elif pot_score > 85 and current_perf < 60: # 潜在能力は高いがまだ実績が低い
                    is_breaking_out = True

            player_data = {
                'team': team_name, 'name': player_name, 'position': pos,
                'age': age, 'years_in_pro': years,
                'current_performance': current_perf, 'potential_score': pot_score,
                'batting_avg': batting_avg, 'home_runs': home_runs, 'era': era,
                'perf_area': int(perf_area), 'pot_area': int(pot_area),
                'convergence_rate': round((convergence * 100), 1),
                'perf_axes_json': json.dumps(perf_axes), 'pot_axes_json': json.dumps(pot_axes),
                'fielding_json': json.dumps(f_positions), 'farm_stats_json': json.dumps(p_farm),
                'similarity_name': sim_name, 'similarity_score': sim_score,
                'style_tag': style_tag,
                'is_breaking_out': is_breaking_out,
                'ghost_axes_json': json.dumps(ghost_axes),
                'is_awakened': is_awakened,
                'is_unbalanced': is_unbalanced,
                'image_url': f'https://api.dicebear.com/7.x/avataaars/svg?seed={player_name}'
            }
            team_players.append(player_data)
            time.sleep(0.01)
            
        save_draft_cache(draft_cache)
        all_players_collected.extend(team_players)
        logger.info(f'Collected {len(team_players)} players for {team_name}')
        time.sleep(0.1)

    database.save_players(all_players_collected)
    logger.info(f'Total {len(all_players_collected)} players saved to database.')

if __name__ == '__main__':
    scrape_real_data()
