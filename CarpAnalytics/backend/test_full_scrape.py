import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))

import scraper
import database
import json

def test_full_scrape_carp():
    print("Scraping Carp data...")
    scraper.scrape_real_data('c')
    
    print("\nChecking Sakakura in DB...")
    players = database.get_all_players()
    sakakura = next((p for p in players if p['name'] == '坂倉将吾'), None)
    if sakakura:
        print(f"Name: {sakakura['name']}")
        print(f"Current Performance: {sakakura['current_performance']}")
        print(f"Fielding JSON: {sakakura['fielding_json']}")
    else:
        print("Sakakura not found in DB.")

if __name__ == "__main__":
    test_full_scrape_carp()
