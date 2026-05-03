# モックとしての潜在能力算出エンジン
# 実際には、年齢、二軍でのスタッツ、フィジカルデータなどを組み合わせて計算します。

def calculate_potential(age: int, years_in_pro: int, current_performance: float, position: str) -> float:
    """
    選手のポテンシャルを年齢・プロ年数・現在実績・ポジションから計算する。
    """
    # 基準点は現在実績をベースにする（実績がある程度ある選手は底上げされる）
    base_potential = current_performance * 0.6 + 30.0
    
    # 年齢による伸び代（24歳をピークの入り口とし、若いほど加点）
    if age < 24:
        base_potential += (24 - age) * 3.5
    elif age > 32:
        # 32歳を超えるとフィジカル面でのポテンシャルは低下
        base_potential -= (age - 32) * 2.5
        
    # プロ年数に対する実績の早熟度
    if years_in_pro < 3 and current_performance > 60:
        # 入団3年以内で高い実績を出している場合は、天井が非常に高いと判断
        base_potential += 10.0
        
    # ポジションによる希少価値（守備負担の大きいポジションへのボーナス）
    pos_bonus = 0.0
    if '捕手' in position or '遊撃手' in position:
        pos_bonus = 5.0
    elif '二塁手' in position or '中堅手' in position:
        pos_bonus = 3.0
    
    base_potential += pos_bonus

    return max(0.0, min(100.0, base_potential))

def calculate_current_performance(
    batting_avg: float = None, 
    home_runs: int = None, 
    era: float = None,
    defense: int = 50,
    speed: int = 50
) -> float:
    """
    現在の実績を0〜100のスコアに変換する。守備力・走力も加味。
    """
    score = 50.0
    
    # 野手の場合
    if batting_avg is not None and (batting_avg > 0 or home_runs > 0):
        # 打撃スコア (打率 0.4 + 本塁打 0.3)
        avg_score = ((max(0.180, min(0.350, batting_avg)) - 0.180) / (0.350 - 0.180)) * 100
        hr_score = (min(home_runs or 0, 40) / 40.0) * 100
        
        # 総合スコア = 打撃 70% + 守備 15% + 走力 15%
        score = (avg_score * 0.4) + (hr_score * 0.3) + (defense * 0.15) + (speed * 0.15)
        
    # 投手の場合
    elif era is not None and era > 0:
        # 防御率スコア (低いほど良い)
        era_clamped = max(1.20, min(7.00, era))
        era_score = 100 - ((era_clamped - 1.20) / (7.00 - 1.20)) * 100
        
        # 投手は防御率重視 (80%) + 守備/フィールディング (20%)
        score = (era_score * 0.8) + (defense * 0.1) + (speed * 0.1)
        
    return max(0.0, min(100.0, score))
