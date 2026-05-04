import database
import potential_engine
import json
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_players_from_db():
    logger.info("Updating player metrics from latest season stats...")
    players = database.get_all_players()
    updated_players = []
    
    for p in players:
        player_name = p['name']
        age = p.get('age', 25)
        years = p.get('years_in_pro', 5)
        pos = p['position']
        
        stats = database.get_player_season_stats(player_name)
        batting = next((s for s in stats if s['stat_type'] == 'batting'), None)
        pitching = next((s for s in stats if s['stat_type'] == 'pitching'), None)
        
        batting_avg = batting['batting_avg'] if batting else None
        home_runs = batting['home_runs'] if batting else None
        era = pitching['era'] if pitching else None
        
        p_farm = json.loads(p['farm_stats_json']) if p.get('farm_stats_json') else {}
        f_positions = json.loads(p['fielding_json']) if p.get('fielding_json') else {}
        
        current_perf = potential_engine.calculate_current_performance(
            batting_avg=batting_avg,
            home_runs=home_runs,
            era=era,
            positions_data=f_positions,
            farm_stats=p_farm,
            speed=50 
        )
        
        pot_score = potential_engine.calculate_potential_score(
            age=age, years_in_pro=years, current_performance=current_perf, position=pos
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
        pot_axes = [max(10, min(100, pot_score)) for _ in range(5)]
        
        perf_area = potential_engine.calculate_chart_area(perf_axes)
        pot_area = potential_engine.calculate_chart_area(pot_axes)
        
        is_unbalanced = (max(perf_axes) - min(perf_axes)) > 40

        rbi = batting['rbi'] if batting else 0
        is_clutch = False
        if not era and batting:
            expected_rbi = (home_runs or 0) * 1.5 + 5
            if rbi > expected_rbi and rbi > 10:
                is_clutch = True
        elif era:
            wins = pitching['wins'] if pitching else 0
            if era < 3.0 and wins > 3:
                is_clutch = True

        convergence = (perf_area / pot_area) if pot_area > 0 else 0
        is_awakened = convergence > 0.82 or is_clutch

        is_breaking_out = False
        if age <= 25:
            if 0.65 < convergence <= 0.82:
                is_breaking_out = True
            elif pot_score > 85 and current_perf < 60:
                is_breaking_out = True

        player_data = {
            'team': p['team'], 'name': player_name, 'position': pos,
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
            'image_url': p['image_url']
        }
        updated_players.append(player_data)
        
    database.save_players(updated_players)
    logger.info(f"Updated {len(updated_players)} players in DB.")

if __name__ == '__main__':
    update_players_from_db()
