import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'CarpAnalytics', 'backend'))
import potential_engine

try:
    perf = potential_engine.calculate_current_performance(
        batting_avg=0.385,
        home_runs=9,
        ops=1.228,
        team_games=33,
        plate_appearances=142
    )
    print(f"Result: {perf}")
except Exception as e:
    import traceback
    traceback.print_exc()
