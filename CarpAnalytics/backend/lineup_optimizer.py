import database
import json
import re
from typing import List, Dict, Any

def get_optimized_lineup(team_name: str = "広島東洋カープ"):
    # 1. データの取得
    all_players = database.get_all_players()
    team_players = [p for p in all_players if team_name in p['team']]
    
    # 成績データの取得
    batter_stats = {s['player_name']: s for s in database.get_season_stats(team=team_name, stat_type='batting')}
    pitcher_stats = {s['player_name']: s for s in database.get_season_stats(team=team_name, stat_type='pitching')}
    
    # 2. 選手情報の整理（守備位置と能力）
    batters = []
    pitchers = []
    
    for p in team_players:
        name = p['name']
        # ポジションの抽出
        positions = []
        if p.get('fielding_json'):
            try:
                fielding = json.loads(p['fielding_json'])
                positions = list(fielding.keys())
            except:
                pass
        
        if not positions:
            # 漢字のポジション名を正規化
            pos = p['position']
            if '投手' in pos: positions.append('投手')
            if '捕手' in pos: positions.append('捕手')
            if '内野手' in pos: positions.extend(['一塁手', '二塁手', '三塁手', '遊撃手']) # 内野手は一通り可能と仮定
            if '外野手' in pos: positions.extend(['左翼手', '中堅手', '右翼手'])
        
        # 投手と野手に分ける
        if '投手' in positions:
            stat = pitcher_stats.get(name, {})
            p['era'] = stat.get('era') if stat.get('era') is not None else 9.99
            p['ip'] = stat.get('innings_pitched') if stat.get('innings_pitched') is not None else 0
            p['wins'] = stat.get('wins') if stat.get('wins') is not None else 0
            # 先発適性スコア (投球回数と防御率で評価)
            p['starter_score'] = (p['ip'] * 2) - (p['era'] * 5)
            pitchers.append(p)
        
        # 野手としての評価
        stat = batter_stats.get(name, {})
        p['ops'] = stat.get('ops') if stat.get('ops') is not None else 0
        p['obp'] = stat.get('on_base_pct') if stat.get('on_base_pct') is not None else 0
        p['slg'] = stat.get('slg_pct') if stat.get('slg_pct') is not None else 0
        p['avg'] = stat.get('batting_avg') if stat.get('batting_avg') is not None else 0
        p['hr'] = stat.get('home_runs') if stat.get('home_runs') is not None else 0
        p['possible_positions'] = [pos for pos in positions if pos != '投手']
        if p['possible_positions'] or '投手' not in positions:
            batters.append(p)

    # 3. 先発ローテーション4人の選出
    rotation = sorted(pitchers, key=lambda x: x['starter_score'], reverse=True)[:4]
    
    # 4. スタメン守備配置の最適化 (Greedy + Backtracking 簡易版)
    # ポジションリスト (投手を除く8ポジション)
    target_positions = ['捕手', '一塁手', '二塁手', '三塁手', '遊撃手', '左翼手', '中堅手', '右翼手']
    
    best_lineup = {}
    used_players = set()
    
    # OPS順にソートして、守備位置を埋めていく
    sorted_batters = sorted(batters, key=lambda x: x['ops'], reverse=True)
    
    # 簡易的なポジション割り当てロジック
    # 1. 専門性の高いポジションから埋める (捕手 -> 遊撃手 -> ...)
    priority_pos = ['捕手', '遊撃手', '二塁手', '三塁手', '一塁手', '中堅手', '右翼手', '左翼手']
    
    for pos in priority_pos:
        for p in sorted_batters:
            if p['name'] not in used_players and pos in p['possible_positions']:
                best_lineup[pos] = p
                used_players.add(p['name'])
                break
    
    # 5. 打順の決定 (セイバーメトリクス流)
    lineup_list = []
    # スタメン9人を決定 (野手8人 + その日の先発1人)
    starters = list(best_lineup.values())
    # 控えからOPSが高い順に補充（もし8人埋まらなかった場合）
    for p in sorted_batters:
        if len(starters) >= 8: break
        if p['name'] not in used_players:
            starters.append(p)
            used_players.add(p['name'])
            
    # 打順テンプレート
    # 1番: 高出塁率
    # 2番: 高出塁率
    # 3番: 最強打者 (最高OPS)
    # 4番: 長打力
    # 5番: 長打力
    # 6-8番: 残り
    # 9番: 投手
    
    batting_order = [None] * 9
    rem_starters = sorted(starters, key=lambda x: x['ops'], reverse=True)
    
    # 3番 (最高OPS)
    if rem_starters: batting_order[2] = rem_starters.pop(0)
    # 4番 (残りで最高SLG)
    rem_starters.sort(key=lambda x: x['slg'], reverse=True)
    if rem_starters: batting_order[3] = rem_starters.pop(0)
    # 1番 (残りで最高OBP)
    rem_starters.sort(key=lambda x: x['obp'], reverse=True)
    if rem_starters: batting_order[0] = rem_starters.pop(0)
    # 2番 (残りで最高OBP)
    if rem_starters: batting_order[1] = rem_starters.pop(0)
    # 5番 (残りで最高SLG)
    rem_starters.sort(key=lambda x: x['slg'], reverse=True)
    if rem_starters: batting_order[4] = rem_starters.pop(0)
    # 6,7,8番 (残り)
    rem_starters.sort(key=lambda x: x['ops'], reverse=True)
    for i in [5, 6, 7]:
        if rem_starters: batting_order[i] = rem_starters.pop(0)
    
    # 9番 (先発投手 - ローテの1番手を仮定)
    if rotation:
        batting_order[8] = rotation[0]

    return {
        "team": team_name,
        "batting_order": [
            {
                "order": i + 1,
                "name": p['name'] if p else "未定",
                "position": next((k for k, v in best_lineup.items() if v['name'] == p['name']), "投手") if p else "N/A",
                "avg": p.get('avg', 0) if p else 0,
                "ops": p.get('ops', 0) if p else 0,
                "hr": p.get('hr', 0) if p else 0
            } for i, p in enumerate(batting_order)
        ],
        "rotation": [
            {
                "rank": i + 1,
                "name": p['name'],
                "era": p['era'],
                "wins": p['wins'],
                "ip": p['ip']
            } for i, p in enumerate(rotation)
        ]
    }

if __name__ == "__main__":
    result = get_optimized_lineup()
    print(json.dumps(result, indent=2, ensure_ascii=False))
