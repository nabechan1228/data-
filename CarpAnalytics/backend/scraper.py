import requests
from bs4 import BeautifulSoup
import pandas as pd
import database
import potential_engine
import stats_scraper
import time
import re

def scrape_real_data(target_team_code=None):
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
        if target_team_code and team_code != target_team_code:
            continue
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
                    
                    # --- 実データの取得（season_stats_2026テーブルから） ---
                    stats = database.get_player_season_stats(player_name)
                    
                    # デフォルト値
                    batting_avg = 0.0
                    home_runs = 0
                    era = None
                    putouts = 0
                    assists = 0
                    errors = 0
                    triples = 0
                    stolen_bases = 0
                    stolen_base_caught = 0
                    games = 0
                    
                    if stats:
                        # 打撃成績または投手成績の最新（あるいは合計）を使用
                        s = stats[0] # 一旦最初のレコードを使用
                        batting_avg = s.get('batting_avg') or 0.0
                        home_runs = s.get('home_runs') or 0
                        era = s.get('era')
                        putouts = s.get('putouts') or 0
                        assists = s.get('assists') or 0
                        errors = s.get('errors') or 0
                        triples = s.get('triples') or 0
                        stolen_bases = s.get('stolen_bases') or 0
                        stolen_base_caught = s.get('stolen_base_caught') or 0
                        games = s.get('games') or 0
                    
                    # 特例補正（スター選手等、データが少ない場合の救済措置）
                    overrides = {
                        '菊池 涼介': {'putouts': 250, 'assists': 450}, 
                        '源田 壮亮': {'putouts': 200, 'assists': 480},
                    }
                    if player_name in overrides:
                        for k, v in overrides[player_name].items():
                            if k == 'putouts': putouts = v
                            elif k == 'assists': assists = v

                    player_data = {
                        "team": team_name,
                        "name": player_name,
                        "position": position,
                        "age": age,
                        "years_in_pro": years_in_pro,
                        "batting_avg": batting_avg,
                        "home_runs": home_runs,
                        "era": era,
                        "putouts": putouts,
                        "assists": assists,
                        "errors": errors,
                        "triples": triples,
                        "stolen_base_caught": stolen_base_caught,
                        "image_url": f"https://placehold.co/150x150/FF0000/FFFFFF?text={i}"
                    }
                    
                    # 守備・走力スコアの算出
                    defense_stats = {
                        "put_outs": putouts, 
                        "assists": assists, 
                        "games": games,
                        "pos": position
                    }
                    sb_rate = stolen_bases / (stolen_bases + stolen_base_caught) if (stolen_bases + stolen_base_caught) > 0 else 0.0
                    speed_stats = {"stolen_bases": stolen_bases, "triples": triples, "success_rate": sb_rate}
                    
                    # エンジンによる算出
                    farm_stats = None 
                    
                    player_data['current_performance'] = potential_engine.calculate_current_performance(
                        batting_avg=batting_avg if games > 0 else None, 
                        home_runs=home_runs, 
                        era=era,
                        defense_stats=defense_stats,
                        speed_stats=speed_stats,
                        farm_stats=farm_stats
                    )
                    
                    sub = potential_engine.calculate_subscores(
                        batting_avg=batting_avg,
                        home_runs=home_runs,
                        era=era,
                        defense_stats=defense_stats,
                        speed_stats=speed_stats
                    )
                    player_data['defense'] = int(sub['defense'])
                    player_data['speed'] = int(sub['speed'])
                    
                    player_data['potential_score'] = potential_engine.calculate_potential(
                        age=age, 
                        years_in_pro=years_in_pro, 
                        current_performance=player_data['current_performance'], 
                        position=position,
                        speed_score=player_data['speed']
                    )

                    import json
                    # ポテンシャル面積と実績面積の計算（5軸: パワー/球威, ミート/制球, スピード/スタミナ, 守備/変化球, 安定感）
                    if not era:
                        # 野手
                        perf_axes = [
                            min(100, (batting_avg or 0) * 300 + 20),
                            min(100, (home_runs or 0) * 5 + 35),
                            sub['speed'],
                            sub['defense'],
                            player_data['current_performance']
                        ]
                        # ポテンシャル軸を個別に動かして個性を出す
                        pot_axes = [
                            min(100, player_data['potential_score'] * 1.1), # 打撃ポテンシャル
                            min(100, player_data['potential_score'] * 1.05), # 長打ポテンシャル
                            max(60, sub['speed'] + (30 - age//2)), # 走力ポテンシャル（年齢で減衰）
                            max(65, sub['defense'] + 10), # 守備ポテンシャル
                            max(70, player_data['current_performance'] + 15) # 安定感ポテンシャル
                        ]
                    else:
                        # 投手
                        # 簡易的なK/9計算（statsがあればそれを使うが、ここではplayer_dataベース）
                        k9_est = 7.5 + (100 - (era or 4.0)*15) / 10
                        perf_axes = [
                            min(100, k9_est * 8),
                            max(0, 100 - (era or 4.0) * 12),
                            50 + (player_data['current_performance'] / 4),
                            sub['defense'],
                            player_data['current_performance']
                        ]
                        pot_axes = [
                            min(100, player_data['potential_score'] * 1.15), # 球威ポテンシャル
                            min(100, player_data['potential_score'] * 1.1),  # 制球ポテンシャル
                            max(60, 100 - age), # スタミナポテンシャル
                            max(70, sub['defense'] + 20), # 変化球・守備
                            max(75, player_data['current_performance'] + 10)
                        ]
                    
                    perf_axes = [max(0, min(100, x)) for x in perf_axes]
                    pot_axes = [max(0, min(100, x)) for x in pot_axes]
                    
                    perf_area = potential_engine.calculate_chart_area(perf_axes)
                    pot_area = potential_engine.calculate_chart_area(pot_axes)
                    
                    player_data['perf_area'] = int(perf_area)
                    player_data['pot_area'] = int(pot_area)
                    player_data['convergence_rate'] = round((perf_area / pot_area * 100), 1) if pot_area > 0 else 0
                    
                    player_data['perf_axes_json'] = json.dumps(perf_axes)
                    player_data['pot_axes_json'] = json.dumps(pot_axes)
                    
                    avg_others = sum(perf_axes[:2] + [perf_axes[4]]) / 3
                    player_data['is_unbalanced'] = sub['defense'] > avg_others + 20 or sub['speed'] > avg_others + 20
                    
                    players.append(player_data)
                    
                    if i > 0 and i % 20 == 0:
                        print(f"  ...scraped {i} players in {team_name}...")
                        
                except Exception as e:
                    print(f"Error scraping {player_name}: {type(e).__name__} {str(e)[:50]}")
        except Exception as e:
            print(f"Error accessing {team_name} roster: {type(e).__name__} {str(e)[:50]}")
            
    return players

def main():
    print("Starting full data update...")
    # 1. 統計データの最新化
    stats_scraper.scrape_all_stats()
    
    # 2. 選手マスターデータの更新（統計データを参照して計算）
    database.init_db()
    players = scrape_real_data()
    database.save_players(players)
    print(f"Successfully scraped and saved {len(players)} players to the database.")

if __name__ == "__main__":
    main()
