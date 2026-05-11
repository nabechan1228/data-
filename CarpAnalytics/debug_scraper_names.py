import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import stats_scraper

def check_names():
    team_code = 'c'
    batters = stats_scraper.scrape_batting_stats(team_code)
    with open('debug_names.txt', 'w', encoding='utf-8') as f:
        for b in batters:
            f.write(f"{b['player_name']}\n")

if __name__ == "__main__":
    check_names()
