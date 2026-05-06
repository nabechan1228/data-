import sys
import os

# backendディレクトリをパスに追加
sys.path.append(os.path.join(os.getcwd(), 'CarpAnalytics', 'backend'))

import scraper

try:
    print("Updating player metrics in database...")
    scraper.update_players_from_db()
    print("Update complete!")
except Exception as e:
    import traceback
    traceback.print_exc()
