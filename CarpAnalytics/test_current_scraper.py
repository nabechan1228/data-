import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import stats_scraper
import logging

logging.basicConfig(level=logging.INFO)

def test():
    team_code = 'c'
    results = []
    
    results.append(f"Testing batting stats for {team_code}...")
    batters = stats_scraper.scrape_batting_stats(team_code)
    if batters:
        results.append(f"Successfully scraped {len(batters)} batters.")
        results.append(f"First batter: {batters[0]['player_name']}")
    else:
        results.append("Failed to scrape batters.")

    results.append(f"\nTesting fielding stats for {team_code}...")
    fielding = stats_scraper.scrape_fielding_stats(team_code)
    if fielding:
        results.append(f"Successfully scraped fielding data for {len(fielding)} players.")
        first_player = list(fielding.keys())[0]
        results.append(f"First player: {first_player}, Positions: {list(fielding[first_player]['positions'].keys())}")
    else:
        results.append("Failed to scrape fielding data.")

    with open('scraper_test_result.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(results))

if __name__ == "__main__":
    test()
