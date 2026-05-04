import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'CarpAnalytics', 'backend'))
import stats_scraper
import json

def debug_fielding():
    team_code = 'c'
    f = stats_scraper.scrape_fielding_stats(team_code)
    for name, data in f.items():
        if '坂倉' in name:
            print(f"Name: {name}")
            print(f"Positions: {json.dumps(data['positions'], ensure_ascii=False)}")
            return
    print("Sakakura not found, showing first 5:")
    for name, data in list(f.items())[:5]:
        print(f"Name: {name}, Pos: {json.dumps(data['positions'], ensure_ascii=False)}")

if __name__ == "__main__":
    debug_fielding()
