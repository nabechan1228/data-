import sqlite3
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class LineupOptimizer:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_team_players(self, team_name: str) -> List[Dict[str, Any]]:
        # R-4: with文でコネクションリークを防止
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            players = [dict(row) for row in conn.execute(
                "SELECT * FROM players WHERE team = ?", (team_name,)
            ).fetchall()]

        import database
        batter_stats  = {s['player_name']: s for s in database.get_season_stats(team=team_name, stat_type='batting')}
        pitcher_stats = {s['player_name']: s for s in database.get_season_stats(team=team_name, stat_type='pitching')}

        for p in players:
            name = p['name']
            p['fielding_json'] = json.loads(p['fielding_json']) if p.get('fielding_json') else {}
            p['perf_axes_json'] = json.loads(p['perf_axes_json']) if p.get('perf_axes_json') else []
            
            if '投手' in p['position']:
                stat = pitcher_stats.get(name, {})
                p['era_live'] = stat.get('era')
                p['wins'] = stat.get('wins', 0)
                p['ip'] = stat.get('innings_pitched', 0)
                p['saves'] = stat.get('saves', 0)
                p['holds'] = stat.get('holds', 0)
                p['games'] = stat.get('games', 0)
            else:
                stat = batter_stats.get(name, {})
                p['avg_live'] = stat.get('batting_avg', 0)
                p['ops'] = stat.get('ops', 0)
                p['obp'] = stat.get('on_base_pct', 0)
                p['slg'] = stat.get('slg_pct', 0)
                p['hr_live'] = stat.get('home_runs', 0)

        return players

    def optimize_defensive_lineup(self, players: List[Dict[str, Any]], league: str = 'Central') -> Dict[str, Any]:
        pitchers = [p for p in players if '投手' in p['position']]
        if not pitchers:
            pitchers = players
        
        if not pitchers:
            return {} # Return empty dict if no players at all
        
        def get_pitcher_score(p):
            e = p.get('era_live')
            era = float(e) if e is not None else 9.99
            ip = float(p.get('ip', 0))
            wins = int(p.get('wins', 0))
            score = (p['current_performance'] or 0)
            if era < 9.99:
                score += (4.0 - era) * 10
                score += ip * 0.5
                score += wins * 5
            else:
                score -= 100 # Heavy penalty for no 1st team stats
            return score

        best_pitcher = max(pitchers, key=get_pitcher_score)
        
        fielders_pool = [p for p in players if p['id'] != best_pitcher['id']]
        
        if league == 'Pacific':
            def_positions = ["捕手", "一塁手", "二塁手", "三塁手", "遊撃手", "外野手", "外野手", "外野手", "指名打者"]
        else:
            def_positions = ["捕手", "一塁手", "二塁手", "三塁手", "遊撃手", "外野手", "外野手", "外野手"]

        assigned_lineup = {"投手": best_pitcher}
        used_player_ids = {best_pitcher['id']}
        
        priority_pos = ["捕手", "遊撃手", "二塁手", "中堅手", "三塁手", "一塁手", "右翼手", "左翼手", "指名打者"]
        actual_priority = [p for p in priority_pos if p in def_positions or (p in ["左翼手", "中堅手", "右翼手"] and "外野手" in def_positions)]

        for pos in actual_priority:
            target_pos_key = "外野手" if pos in ["左翼手", "中堅手", "右翼手"] else pos
            
            candidates = []
            for p in fielders_pool:
                if p['id'] in used_player_ids: continue
                
                suitability = 0
                f_json = p.get('fielding_json', {})
                
                if pos in f_json or target_pos_key in f_json:
                    suitability = 1.0
                elif pos in p['position'] or target_pos_key in p['position']:
                    suitability = 0.9
                elif target_pos_key == "外野手" and ("外野" in p['position'] or any(x in f_json for x in ["左翼手", "中堅手", "右翼手", "外野手"])):
                    suitability = 0.8
                elif pos == "指名打者":
                    suitability = 0.7
                
                if suitability > 0:
                    performance = p['current_performance'] or 0
                    ops = p.get('ops')
                    ops_bonus = (float(ops) if ops is not None else 0) * 0.5
                    score = (performance + ops_bonus) * suitability
                    candidates.append((score, p))
            
            if candidates:
                candidates.sort(key=lambda x: x[0], reverse=True)
                best_candidate = candidates[0][1]
                
                key = target_pos_key
                if key == "外野手":
                    for i in range(1, 4):
                        if f"外野手{i}" not in assigned_lineup:
                            key = f"外野手{i}"
                            break
                
                assigned_lineup[key] = best_candidate
                used_player_ids.add(best_candidate['id'])

        all_target_keys = []
        for dp in def_positions:
            if dp == "外野手":
                for i in range(1, 4):
                    if f"外野手{i}" not in all_target_keys:
                        all_target_keys.append(f"外野手{i}")
                        break
            else:
                all_target_keys.append(dp)

        for key in all_target_keys:
            if key not in assigned_lineup:
                remaining = [p for p in fielders_pool if p['id'] not in used_player_ids]
                if remaining:
                    remaining.sort(key=lambda x: x['current_performance'] or 0, reverse=True)
                    assigned_lineup[key] = remaining[0]
                    used_player_ids.add(remaining[0]['id'])

        return assigned_lineup

    def determine_batting_order(self, lineup: Dict[str, Any]) -> List[Dict[str, Any]]:
        batters = [p for k, p in lineup.items() if "投手" not in k]
        pitcher = lineup.get("投手")
        if not batters: return []
        
        def get_stat(p, key):
            val = p.get(key)
            return float(val) if val is not None else 0

        order = [None] * 9
        used_ids = set()
        
        batters.sort(key=lambda x: get_stat(x, 'ops'), reverse=True)
        order[2] = batters[0]
        used_ids.add(order[2]['id'])
        
        rem_batters = [b for b in batters if b['id'] not in used_ids]
        rem_batters.sort(key=lambda x: get_stat(x, 'slg'), reverse=True)
        if rem_batters:
            order[3] = rem_batters[0]
            used_ids.add(order[3]['id'])
            
        rem_batters = [b for b in batters if b['id'] not in used_ids]
        rem_batters.sort(key=lambda x: (get_stat(x, 'obp') * 0.7 + (get_stat(x, 'speed') / 100) * 0.3), reverse=True)
        if rem_batters:
            order[0] = rem_batters[0]
            used_ids.add(order[0]['id'])
            
        rem_batters = [b for b in batters if b['id'] not in used_ids]
        rem_batters.sort(key=lambda x: get_stat(x, 'obp'), reverse=True)
        if rem_batters:
            order[1] = rem_batters[0]
            used_ids.add(order[1]['id'])
            
        rem_batters = [b for b in batters if b['id'] not in used_ids]
        rem_batters.sort(key=lambda x: get_stat(x, 'ops'), reverse=True)
        if rem_batters:
            order[4] = rem_batters[0]
            used_ids.add(order[4]['id'])
            
        rem_batters = [b for b in batters if b['id'] not in used_ids]
        rem_batters.sort(key=lambda x: get_stat(x, 'ops'), reverse=True)
        
        for i in [5, 6, 7]:
            if rem_batters:
                order[i] = rem_batters.pop(0)
                used_ids.add(order[i]['id'])
        
        if pitcher and len([p for p in order if p is not None]) < 9:
            order[8] = pitcher
        elif rem_batters:
            order[8] = rem_batters[0]

        result = []
        for i, p in enumerate(order):
            if p:
                pos_name = next((k for k, v in lineup.items() if v['id'] == p['id']), "打者")
                result.append({
                    "order": i + 1,
                    "id": p['id'],
                    "name": p['name'],
                    "position": pos_name,
                    "avg": get_stat(p, 'avg_live'),
                    "ops": get_stat(p, 'ops'),
                    "hr": get_stat(p, 'hr_live'),
                    "current_performance": p.get('current_performance', 0)
                })
        return result

    def get_pitching_staff(self, players: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        pitchers = [p for p in players if '投手' in p['position']]
        if not pitchers: return {"starters": [], "relievers": [], "closer": []}
        
        def get_era(p):
            e = p.get('era_live')
            return float(e) if e is not None else 9.99

        for p in pitchers:
            era = get_era(p)
            ip = p.get('ip', 0)
            wins = p.get('wins', 0)
            games = p.get('games', 0)
            saves = p.get('saves', 0)
            holds = p.get('holds', 0)
            
            score = (p['current_performance'] or 0)
            if era < 9.99:
                score += (4.0 - era) * 10
                score += ip * 0.5
                score += wins * 5
                score += saves * 10
                score += holds * 5
            else:
                score -= 100 # Huge penalty for no 1st team stats
            
            p['pitcher_score'] = score
            
            # Roles based on actual stats
            ip_per_game = ip / games if games > 0 else 0
            is_starter_material = ip_per_game >= 3.0 or wins >= 3

            if saves >= 1 and saves > holds and not is_starter_material:
                p['role'] = 'closer'
            elif is_starter_material:
                p['role'] = 'starter'
            else:
                p['role'] = 'reliever'

        # Sort all by score
        active_pitchers = sorted(pitchers, key=lambda x: x['pitcher_score'], reverse=True)
        
        starters = [p for p in active_pitchers if p.get('role') == 'starter']
        closers = [p for p in active_pitchers if p.get('role') == 'closer']
        relievers = [p for p in active_pitchers if p.get('role') == 'reliever']
        
        # Fallback if categories are empty
        if len(starters) < 6:
            needed = 6 - len(starters)
            available = [p for p in relievers if p not in starters][:needed]
            starters.extend(available)
            relievers = [p for p in relievers if p not in available]
            
        if not closers and relievers:
            closers = [relievers.pop(0)]
            
        # Ensure we just take the top ones
        starters = sorted(starters, key=lambda x: x['pitcher_score'], reverse=True)[:6]
        relievers = sorted(relievers, key=lambda x: x['pitcher_score'], reverse=True)[:6]
        closer = closers[:1] if closers else []
        
        def _pitcher_data(p):
            return {
                "name": p['name'],
                "era": get_era(p),
                "wins": p.get('wins', 0),
                "games": p.get('games', 0),
                "ip": p.get('ip', 0),
                "holds": p.get('holds', 0),
                "saves": p.get('saves', 0),
                "perf": p['current_performance'],
                "image_url": p.get('image_url')
            }
        
        return {
            "starters": [_pitcher_data(p) for p in starters],
            "relievers": [_pitcher_data(p) for p in relievers],
            "closer": [_pitcher_data(p) for p in closer]
        }

def get_optimized_team_data(team_name: str, db_path: str):
    from stats_scraper import LEAGUE_MAP, TEAM_CODE_MAP
    optimizer = LineupOptimizer(db_path)
    players = optimizer.get_team_players(team_name)
    team_code = next((k for k, v in TEAM_CODE_MAP.items() if v == team_name), 'c')
    league = LEAGUE_MAP.get(team_code, 'Central')
    def_lineup = optimizer.optimize_defensive_lineup(players, league)
    batting_order = optimizer.determine_batting_order(def_lineup)
    pitching_staff = optimizer.get_pitching_staff(players)
    
    return {
        "team": team_name,
        "league": league,
        "defensive_lineup": {k: {"name": v["name"], "id": v["id"], "image_url": v.get("image_url")} for k, v in def_lineup.items()},
        "batting_order": batting_order,
        "pitching_staff": pitching_staff
    }
