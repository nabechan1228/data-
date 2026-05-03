# モックとしての潜在能力算出エンジン
# 実際には、年齢、二軍でのスタッツ、フィジカルデータなどを組み合わせて計算します。

def calculate_potential(age: int, years_in_pro: int, current_performance: float, position: str) -> float:
    """
    選手のポテンシャル（将来性・潜在能力）を0〜100のスコアで算出するモックロジック。
    若くて実績が少ないほど「上振れ」のポテンシャルが高く出やすい設計。
    """
    base_potential = 70.0
    
    # 若さは正義（年齢が若いほどポテンシャルが高い）
    if age < 23:
        base_potential += 20
    elif age < 27:
        base_potential += 10
    elif age > 33:
        base_potential -= 15
        
    # プロ年数が短いのに実績が出ている＝天才肌
    if years_in_pro < 3 and current_performance > 50:
        base_potential += 15
        
    # すでに実績が完成されているベテランはポテンシャル＝実績に近づく
    if age > 30 and current_performance > 70:
        base_potential = current_performance + 5

    # 上限下限クリップ
    return max(0.0, min(100.0, base_potential))

def calculate_current_performance(batting_avg: float = None, home_runs: int = None, era: float = None) -> float:
    """
    現在の成績を0〜100のスコアに変換するモックロジック。
    """
    score = 50.0 # 平均
    if batting_avg is not None:
        if batting_avg > 0.300: score += 30
        elif batting_avg > 0.270: score += 15
        elif batting_avg < 0.230: score -= 20
        
        if home_runs and home_runs > 15: score += 20
            
    if era is not None:
        if era < 2.00: score += 40
        elif era < 3.00: score += 20
        elif era > 4.50: score -= 20
        
    return max(0.0, min(100.0, score))
