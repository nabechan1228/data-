import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'backend'))
import potential_engine

def test_engine():
    print("--- 1. Testing Current Performance ---")
    # Standard player
    perf_basic = potential_engine.calculate_current_performance(batting_avg=0.280, home_runs=15, defense=50, speed=50)
    print(f"Basic Player (.280, 15HR): {perf_basic:.1f}")
    
    # Detailed stats
    speed_stats = {"stolen_bases": 20, "triples": 5, "success_rate": 0.8}
    defense_stats = {"put_outs": 200, "assists": 10, "innings": 800}
    perf_detailed = potential_engine.calculate_current_performance(
        batting_avg=0.280, home_runs=15, 
        defense_stats=defense_stats, 
        speed_stats=speed_stats
    )
    print(f"Detailed Stats Player: {perf_detailed:.1f}")

    print("\n--- 2. Testing Potential Aging Curves ---")
    # 35 year old Catcher vs 35 year old Outfielder (Speedster)
    perf = 70.0
    catcher_pot = potential_engine.calculate_potential(age=35, years_in_pro=15, current_performance=perf, position="捕手")
    outfielder_pot = potential_engine.calculate_potential(age=35, years_in_pro=15, current_performance=perf, position="外野手", speed_score=85)
    
    print(f"35yo Catcher Potential: {catcher_pot:.1f}")
    print(f"35yo Speedster Potential: {outfielder_pot:.1f}")
    print(f"Difference: {catcher_pot - outfielder_pot:.1f}")

    print("\n--- 3. Testing Situational Bonuses ---")
    situational = {"is_clutch": True, "early_count_aggressiveness": 0.7}
    normal_pot = potential_engine.calculate_potential(age=25, years_in_pro=5, current_performance=perf, position="内野手")
    bonus_pot = potential_engine.calculate_potential(age=25, years_in_pro=5, current_performance=perf, position="内野手", situational_data=situational)
    
    print(f"Normal Potential: {normal_pot:.1f}")
    print(f"Bonus Potential: {bonus_pot:.1f}")
    print(f"Bonus added: {bonus_pot - normal_pot:.1f}")

if __name__ == "__main__":
    test_engine()
