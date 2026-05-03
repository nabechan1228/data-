# モックとしての潜在能力算出エンジン
# 実際には、年齢、二軍でのスタッツ、フィジカルデータなどを組み合わせて計算します。

def calculate_potential(age: int, years_in_pro: int, current_performance: float, position: str) -> float:
    """
    選手のポテンシャルを年齢・プロ年数・現在実績から連続的に計算する。
    """
    # 基準点は現在実績をベースにしつつ、年齢による伸び代を加味
    base_potential = current_performance * 0.5 + 40.0
    
    # 年齢によるポテンシャル補正（若いほど高く、30歳を超えると徐々に低下）
    if age < 25:
        base_potential += (25 - age) * 2.5
    elif age > 30:
        base_potential -= (age - 30) * 2.0
        
    # プロ年数が短いのに実績が出ている場合（天才肌ボーナス）
    if years_in_pro < 5:
        base_potential += (current_performance / 100.0) * (5 - years_in_pro) * 3.0

    return max(0.0, min(100.0, base_potential))

def calculate_current_performance(batting_avg: float = None, home_runs: int = None, era: float = None) -> float:
    """
    現在の成績を0〜100のスコアに連続値として変換する。
    """
    score = 50.0
    
    if batting_avg is not None and batting_avg > 0:
        # 打率 0.200 〜 0.330 を 30 〜 80 にマッピング
        avg_score = ((batting_avg - 0.200) / (0.330 - 0.200)) * 50 + 30
        
        # 本塁打 0 〜 30 を 0 〜 20 にマッピング
        hr_score = (min(home_runs or 0, 30) / 30.0) * 20
        
        score = avg_score + hr_score
        
    elif era is not None and era > 0:
        # 防御率 5.00 〜 1.50 を 30 〜 90 にマッピング（低い方が高スコア）
        # era が 5.0 以上の場合は 30 以下になる
        era_clamped = max(1.50, min(6.00, era))
        score = 90 - ((era_clamped - 1.50) / (6.00 - 1.50)) * 60
        
    return max(0.0, min(100.0, score))
