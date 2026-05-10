import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'CarpAnalytics', 'backend'))
import scraper
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("Updating all player scores in database...")
    scraper.update_players_from_db()
    print("Update complete.")
