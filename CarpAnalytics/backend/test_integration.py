import database
import stats_scraper
import scraper
import logging

logging.basicConfig(level=logging.INFO)

def test_flow():
    # 1. 広島東洋カープの統計データのみ取得
    print("Fetching stats for Hiroshima...")
    database.ensure_stats_table()
    stats = stats_scraper.scrape_batting_stats('c')
    fielding = stats_scraper.scrape_fielding_stats('c')
    
    # マージ
    print(f"Sample names in batting stats: {[s['player_name'] for s in stats[:5]]}")
    print(f"Sample names in fielding stats: {list(fielding.keys())[:5]}")
    for s in stats:
        norm = stats_scraper.normalize_name(s['player_name'])
        f = fielding.get(norm)
        if f:
            s['putouts'] = f['putouts']
            s['assists'] = f['assists']
            s['errors'] = f['errors']
        else:
            if "菊池" in s['player_name']:
                print(f"Match failed for {s['player_name']} (normalized: {norm})")
    
    database.save_season_stats(stats)
    print(f"Saved {len(stats)} stats records.")

    # 2. 選手データを1人だけチェック
    player_name = "菊池　涼介"
    print(f"Checking potential for {player_name}...")
    
    # scraper.py のロジックを一部抜粋してテスト
    stats_from_db = database.get_player_season_stats(player_name)
    if stats_from_db:
        s = stats_from_db[0]
        print(f"Stats found: PO={s['putouts']}, ASST={s['assists']}, AVG={s['batting_avg']}")
        
        import potential_engine
        defense_stats = {"put_outs": s['putouts'], "assists": s['assists'], "games": s['games']}
        speed_stats = {"stolen_bases": s['stolen_bases'], "triples": s['triples'], "success_rate": 0.8}
        
        perf = potential_engine.calculate_current_performance(
            batting_avg=s['batting_avg'],
            home_runs=s['home_runs'],
            defense_stats=defense_stats,
            speed_stats=speed_stats
        )
        pot = potential_engine.calculate_potential(
            age=36, 
            years_in_pro=15, 
            current_performance=perf, 
            position="二塁手"
        )
        print(f"Performance Score: {perf:.2f}")
        print(f"Potential Score: {pot:.2f}")

if __name__ == "__main__":
    test_flow()
