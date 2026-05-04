import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import stats_scraper
import database

def test_fielding():
    print("Testing fielding scraper for 'c' (Carp)...")
    data = stats_scraper.scrape_fielding_stats('c')
    
    # Check some players
    # 坂倉 (Sakakura) is likely a catcher and potentially others
    sakakura = data.get('坂倉将吾')
    if sakakura:
        print(f"Sakakura: {sakakura}")
    else:
        print("Sakakura not found. All players found:")
        print(list(data.keys())[:5])

    # Check aggregation in scrape_all_stats logic
    batters = stats_scraper.scrape_batting_stats('c', 27)
    for b in batters[:5]:
        name = stats_scraper.normalize_name(b['player_name'])
        f = data.get(name)
        if f and 'positions' in f:
            po = sum(p.get('putouts', 0) for p in f['positions'].values())
            print(f"Player: {name}, Putouts: {po}")

if __name__ == "__main__":
    test_fielding()
