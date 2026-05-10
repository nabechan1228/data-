import database
import json
import sys

# Windowsでの文字化け対策
sys.stdout.reconfigure(encoding='utf-8')

players = database.get_all_players()
carp_players = [p for p in players if '広島' in p['team']]

print("--- 広島東洋カープ 選手ポジション一覧 ---")
for p in carp_players:
    # ポジション情報の詳細を確認（fielding_jsonがある場合はそれも）
    fielding = {}
    if p.get('fielding_json'):
        try:
            fielding = json.loads(p['fielding_json'])
        except:
            pass
    
    pos_info = p['position']
    if fielding:
        # fielding_jsonに複数の守備位置情報があるか確認
        positions = list(fielding.keys())
        if positions:
            pos_info += f" (詳細: {', '.join(positions)})"
            
    print(f"{p['name']}: {pos_info}")

print("\n--- 投手成績（先発候補） ---")
stats = database.get_season_stats(team='広島東洋カープ', stat_type='pitching')
# 投球回の多い順に並べて表示
for s in sorted(stats, key=lambda x: x.get('innings_pitched', 0), reverse=True)[:10]:
    print(f"{s['player_name']}: 防御率{s['era']}, 投球回{s['innings_pitched']}, 勝利{s['wins']}")
