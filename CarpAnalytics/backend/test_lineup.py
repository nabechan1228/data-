import lineup_engine
import os
import json

DB_PATH = "carp_data.db"

def test():
    team = "広島東洋カープ"
    print(f"Testing for {team}...")
    
    data = lineup_engine.get_optimized_team_data(team, DB_PATH)
    
    print("\n--- Defensive Lineup ---")
    for pos, p in data['defensive_lineup'].items():
        print(f"{pos}: {p['name']} ({p['position']}) - Perf: {p['current_performance']}")
        
    print("\n--- Batting Order ---")
    for i, p in enumerate(data['batting_order']):
        print(f"{i+1}. {p['name']} - AVG: {p.get('batting_avg')}, HR: {p.get('home_runs')}")
        
    print("\n--- Pitching Staff ---")
    print("Starters:")
    for p in data['pitching_staff']['starters']:
        print(f"  {p['name']} - ERA: {p.get('era')}, Perf: {p['current_performance']}")
    
    print("Closer:")
    for p in data['pitching_staff']['closer']:
        print(f"  {p['name']}")

if __name__ == "__main__":
    test()
