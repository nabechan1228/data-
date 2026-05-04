import math

# ロールモデル（レジェンド）の定義
LEGENDS = {
    'イチロー': [95, 60, 98, 99, 95], # パワー, ミート, スピード, 守備, 安定感
    '大谷翔平': [99, 92, 85, 70, 90],
    '王貞治':   [99, 85, 50, 75, 99],
    '村上宗隆': [98, 80, 45, 65, 85],
    '近本光司': [65, 85, 98, 95, 90],
    '山本由伸': [98, 95, 70, 85, 95], # 球威, 制球, スタミナ, 守備/変化, 安定感
    'ダルビッシュ': [95, 90, 80, 95, 90],
    '菅野智之': [85, 99, 85, 90, 95],
}

def calculate_cosine_similarity(v1, v2):
    """2つのベクトルのコサイン類似度を計算 (0.0 - 1.0)"""
    if not v1 or not v2 or len(v1) != len(v2): return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a**2 for a in v1))
    mag2 = math.sqrt(sum(b**2 for b in v2))
    if mag1 == 0 or mag2 == 0: return 0.0
    return dot_product / (mag1 * mag2)

def find_best_role_model(axes, is_pitcher):
    """最も類似したレジェンドを選出する"""
    best_score = -1.0
    best_name = "未定義"
    best_axes = [50, 50, 50, 50, 50]
    
    # 候補のフィルタリング
    candidates = {}
    if is_pitcher:
        # 投手レジェンド
        candidates = {k: v for k, v in LEGENDS.items() if k in ['山本由伸', 'ダルビッシュ', '菅野智之']}
    else:
        # 野手レジェンド
        candidates = {k: v for k, v in LEGENDS.items() if k in ['イチロー', '王貞治', '大谷翔平', '村上宗隆', '近本光司']}
    
    if not candidates:
        candidates = LEGENDS # フォールバック
        
    for name, legend_axes in candidates.items():
        score = calculate_cosine_similarity(axes, legend_axes)
        if score > best_score:
            best_score = score
            best_name = name
            best_axes = legend_axes
            
    return best_name, round(best_score * 100, 1), best_axes

def calculate_chart_area(values):
    """
    正五角形のレーダーチャートの面積を計算する。
    各頂点の値を v1, v2, v3, v4, v5 とすると、
    面積 S = 1/2 * sin(72度) * (v1*v2 + v2*v3 + v3*v4 + v4*v5 + v5*v1)
    """
    if len(values) < 5:
        return 0
    
    sin72 = math.sin(math.radians(72))
    area = 0.5 * sin72 * (
        values[0]*values[1] + 
        values[1]*values[2] + 
        values[2]*values[3] + 
        values[3]*values[4] + 
        values[4]*values[0]
    )
    return area

def calculate_subscores(positions_data=None, batting_avg=None, home_runs=None, era=None, speed_score=50):
    """
    守備・走力のサブスコアを算出。
    マルチポジション対応：各ポジションの出場試合数で加重平均してRFを算出。
    """
    RF_AVG = {
        '投手': 1.5, '捕手': 6.0, '一塁手': 8.5, '二塁手': 4.5,
        '三塁手': 3.0, '遊撃手': 4.5, '外野手': 2.0
    }
    
    defense_score = 50.0
    
    if positions_data and isinstance(positions_data, dict):
        total_weighted_score = 0
        total_games = 0
        
        for pos, stats in positions_data.items():
            avg_rf = RF_AVG.get(pos, 3.0)
            games = stats.get('games', 0)
            if games > 0:
                rf = (stats.get('putouts', 0) + stats.get('assists', 0)) / games
                pos_score = (rf / avg_rf) * 50 + 25
                total_weighted_score += pos_score * games
                total_games += games
        
        if total_games > 0:
            defense_score = total_weighted_score / total_games
    
    return {
        'defense': max(0, min(100, defense_score)),
        'speed': max(0, min(100, speed_score))
    }

def calculate_current_performance(
    batting_avg: float = None, 
    home_runs: int = None, 
    era: float = None,
    positions_data: dict = None,
    farm_stats: dict = None,
    defense: float = 50.0,
    speed: float = 50.0
) -> float:
    """
    現在の実績を0〜100のスコアに変換する。
    1軍実績がない場合、2軍（ファーム）実績を割り引いて加味する。
    """
    # 2軍実績の統合
    if batting_avg is None and farm_stats:
        # 2軍成績を割り引いて（目安: 80%）1軍相当として扱う
        batting_avg = farm_stats.get('avg', 0.0) * 0.8
        home_runs = farm_stats.get('hr', 0) * 0.7
        # OPSも加味した評価（もしあれば）
        # farm_ops = farm_stats.get('ops', 0.0)
    
    sub = calculate_subscores(positions_data, batting_avg, home_runs, era, speed)
    defense = sub['defense']
    speed = sub['speed']

    score = 50.0
    
    if batting_avg is not None and (batting_avg > 0 or home_runs > 0):
        avg_score = ((max(0.150, min(0.350, batting_avg)) - 0.150) / (0.350 - 0.150)) * 100
        hr_score = (min(home_runs or 0, 40) / 40.0) * 100
        score = (avg_score * 0.30) + (hr_score * 0.20) + (defense * 0.35) + (speed * 0.15)
        
    elif era is not None and era > 0:
        era_clamped = max(1.20, min(7.00, era))
        era_score = 100 - ((era_clamped - 1.20) / (7.00 - 1.20)) * 100
        score = (era_score * 0.8) + (defense * 0.15) + (speed * 0.05)
        
    return max(0.0, min(100.0, score))

def calculate_potential_score(age, years_in_pro, current_performance, batting_avg=None, home_runs=None, era=None, defense=50, speed=50):
    """
    選手の総合的なポテンシャルスコアを算出。
    """
    score = current_performance
    # 期待値としてのポテンシャル
    potential = score + (100 - score) * (1.0 / (1.0 + age * 0.1))
    return max(0.0, min(100.0, potential))
