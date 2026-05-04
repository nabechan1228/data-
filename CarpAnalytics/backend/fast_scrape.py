import scraper
import database

def fast_update():
    print("Running fast update for Hiroshima...")
    try:
        players = scraper.scrape_real_data(target_team_code='c')
        database.save_players(players)
        print(f"Successfully updated {len(players)} players for Hiroshima.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fast_update()
