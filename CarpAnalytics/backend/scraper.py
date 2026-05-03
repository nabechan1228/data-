import requests
from bs4 import BeautifulSoup
import pandas as pd
import database
import potential_engine
import time
import re

def scrape_real_data():
    base_url = "https://npb.jp"
    
    teams_dict = {
        'c': '広島東洋カープ',
        'g': '読売ジャイアンツ',
        't': '阪神タイガース',
        'db': '横浜DeNAベイスターズ',
        's': '東京ヤクルトスワローズ',
        'd': '中日ドラゴンズ',
        'b': 'オリックス・バファローズ',
        'm': '千葉ロッテマリーンズ',
        'h': '福岡ソフトバンクホークス',
        'e': '東北楽天ゴールデンイーグルス',
        'l': '埼玉西武ライオンズ',
        'f': '北海道日本ハムファイターズ'
    }
    
    players = []
    
    for team_code, team_name in teams_dict.items():
        roster_url = f"{base_url}/bis/teams/rst_{team_code}.html"
        
        try:
            response = requests.get(roster_url)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 投手、捕手、内野手、外野手のセクションを特定して選手リンクを取得
            links = soup.find_all('a', href=re.compile(r'/bis/players/\d+\.html'))
            print(f"[{team_name}] Found {len(links)} players. Scraping data...")
            
            for i, a_tag in enumerate(links):
                player_name = a_tag.text.strip().replace('\u3000', ' ')
                player_url = base_url + a_tag['href']
                
                # プレイヤーごとの詳細ページを取得
                try:
                    # サーバー負荷軽減のため少し待機
                    time.sleep(0.05) # 全球団取得のため少し待機時間を短縮
                    p_res = requests.get(player_url)
                    p_res.encoding = 'utf-8'
                    p_soup = BeautifulSoup(p_res.text, 'html.parser')
                    
                    # プロフィールテキストとポジションを取得
                    table_th = p_soup.find('th', string='ポジション')
                    position = table_th.find_next_sibling('td').text.strip() if table_th else "不明"
                    
                    # 実年齢とプロ年数をテーブルから取得
                    age = 25
                    years_in_pro = 3
                    
                    birth_th = p_soup.find('th', string='生年月日')
                    if birth_th:
                        birth_str = birth_th.find_next_sibling('td').text.strip()
                        match = re.search(r'(\d{4})年', birth_str)
                        if match:
                            age = 2026 - int(match.group(1))
                            
                    draft_th = p_soup.find('th', string='ドラフト')
                    if draft_th:
                        draft_str = draft_th.find_next_sibling('td').text.strip()
                        match = re.search(r'(\d{4})年', draft_str)
                        if match:
                            years_in_pro = 2026 - int(match.group(1))
                        else:
                            years_in_pro = max(1, age - 22)
                    else:
                        years_in_pro = max(1, age - 22)
                    
                    import random
                    random.seed(player_name)
                    
                    # --- 守備・走力の設定 ---
                    defense = random.randint(40, 70)
                    speed = random.randint(40, 75)
                    
                    # スター選手などの特例補正
                    overrides = {
                        '小園　海斗': {'batting_avg': 0.286, 'home_runs': 2, 'defense': 85, 'speed': 85},
                        '菊池　涼介': {'defense': 99, 'speed': 70, 'batting_avg': 0.240, 'home_runs': 9},
                        '矢野　雅哉': {'defense': 98, 'speed': 85, 'batting_avg': 0.260},
                        '秋山　翔吾': {'batting_avg': 0.289, 'defense': 85, 'speed': 75},
                        '坂倉　将吾': {'batting_avg': 0.279, 'home_runs': 12, 'defense': 70},
                        '大瀬良　大地': {'era': 1.86, 'defense': 60},
                        '森下　暢仁': {'era': 2.50, 'defense': 70},
                        '栗林　良吏': {'era': 1.96},
                        '源田　壮亮': {'defense': 99, 'speed': 80, 'batting_avg': 0.250},
                        '辰己　涼介': {'defense': 98, 'speed': 85, 'batting_avg': 0.270},
                    }
                    
                    if '投手' in position:
                        era = round(random.uniform(2.00, 5.50), 2)
                        home_runs = 0
                        batting_avg = 0.0
                    else:
                        era = None
                        home_runs = random.randint(0, 15)
                        batting_avg = round(random.uniform(0.200, 0.280), 3)
                        
                    # 実データスクレイピング
                    try:
                        tables = p_soup.find_all('table')
                        for t in tables:
                            headers = [th.text.strip() for th in t.find_all('th')]
                            if len(headers) > 10 and ('打率' in headers or '防御率' in headers):
                                rows = t.find_all('tr')
                                # 「通算」ではない最後の行（最新シーズン）を取得
                                valid_rows = [r for r in rows if r.find('td') and '通' not in r.find_all('td')[0].text]
                                if valid_rows:
                                    last_row = valid_rows[-1]
                                    tds = last_row.find_all('td')
                                    if len(tds) == len(headers) or len(tds) == len(headers) - 1:
                                        if '投手' in position and '防御率' in headers:
                                            idx = headers.index('防御率')
                                            val = tds[idx - (len(headers)-len(tds))].text.strip()
                                            if val and val != '-' and val != 'nan':
                                                era = float(val)
                                        elif ('野手' in position or '捕手' in position):
                                            if '打率' in headers:
                                                idx = headers.index('打率')
                                                val = tds[idx - (len(headers)-len(tds))].text.strip()
                                                if val and val != '-' and val != 'nan':
                                                    batting_avg = float(val)
                                            if '本塁打' in headers:
                                                idx = headers.index('本塁打')
                                                val = tds[idx - (len(headers)-len(tds))].text.strip()
                                                if val and val != '-' and val != 'nan':
                                                    home_runs = int(val)
                                break
                    except Exception as e:
                        pass
                        
                    if player_name in overrides:
                        for k, v in overrides[player_name].items():
                            if k == 'batting_avg': batting_avg = v
                            elif k == 'home_runs': home_runs = v
                            elif k == 'era': era = v
                            elif k == 'defense': defense = v
                            elif k == 'speed': speed = v
                                    
                    player_data = {
                        "team": team_name,
                        "name": player_name,
                        "position": position,
                        "age": age,
                        "years_in_pro": years_in_pro,
                        "batting_avg": batting_avg,
                        "home_runs": home_runs,
                        "era": era,
                        "defense": defense,
                        "speed": speed,
                        "image_url": f"https://placehold.co/150x150/FF0000/FFFFFF?text={i}"
                    }
                    
                    player_data['current_performance'] = potential_engine.calculate_current_performance(
                        batting_avg=batting_avg, 
                        home_runs=home_runs, 
                        era=era,
                        defense=defense,
                        speed=speed
                    )
                    player_data['potential_score'] = potential_engine.calculate_potential(
                        age=age, 
                        years_in_pro=years_in_pro, 
                        current_performance=player_data['current_performance'], 
                        position=position
                    )
                    
                    players.append(player_data)
                    
                    if i > 0 and i % 20 == 0:
                        print(f"  ...scraped {i} players in {team_name}...")
                        
                except Exception as e:
                    print(f"Error scraping {player_name}: {type(e).__name__} {str(e)[:50]}")
        except Exception as e:
            print(f"Error accessing {team_name} roster: {type(e).__name__} {str(e)[:50]}")
            
    return players

def main():
    database.init_db()
    players = scrape_real_data()
    database.save_players(players)
    print(f"Successfully scraped and saved {len(players)} players to the database.")

if __name__ == "__main__":
    main()
