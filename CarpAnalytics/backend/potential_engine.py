import math

# ロールモデル（レジェンド・現役スター）の定義
LEGENDS = {
    # 野手
    'イチロー':     {'axes': [70, 99, 98, 99, 95], 'tag': '安打製造機', 'pitcher': False},
    '大谷翔平':     {'axes': [99, 92, 85, 70, 90], 'tag': '二刀流・超人', 'pitcher': False},
    '王貞治':       {'axes': [99, 85, 50, 75, 99], 'tag': '世界の王', 'pitcher': False},
    '村上宗隆':     {'axes': [98, 80, 45, 65, 85], 'tag': '若き大砲', 'pitcher': False},
    '近本光司':     {'axes': [65, 85, 98, 95, 90], 'tag': 'スピードスター', 'pitcher': False},
    '柳田悠岐':     {'axes': [98, 85, 80, 70, 85], 'tag': 'フルスイング', 'pitcher': False},
    '近藤健介':     {'axes': [75, 98, 60, 70, 95], 'tag': '出塁の達人', 'pitcher': False},
    '周東佑京':     {'axes': [30, 70, 99, 85, 80], 'tag': '韋駄天', 'pitcher': False},
    '源田壮亮':     {'axes': [40, 75, 85, 99, 90], 'tag': '守備職人', 'pitcher': False},
    
    # 投手
    '山本由伸':     {'axes': [98, 95, 70, 85, 95], 'tag': '絶対的エース', 'pitcher': True},
    'ダルビッシュ': {'axes': [95, 90, 80, 95, 90], 'tag': '変幻自在', 'pitcher': True},
    '菅野智之':     {'axes': [85, 99, 85, 90, 95], 'tag': '精密機械', 'pitcher': True},
    '佐々木朗希':   {'axes': [99, 85, 70, 80, 85], 'tag': '令和の怪物', 'pitcher': True},
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
    best_tag = "分析中"
    best_axes = [50, 50, 50, 50, 50]
    
    # 候補のフィルタリング
    candidates = {k: v for k, v in LEGENDS.items() if v['pitcher'] == is_pitcher}
    
    if not candidates:
        candidates = LEGENDS # フォールバック
        
    for name, data in candidates.items():
        legend_axes = data['axes']
        score = calculate_cosine_similarity(axes, legend_axes)
        if score > best_score:
            best_score = score
            best_name = name
            best_tag = data['tag']
            best_axes = legend_axes
            
    return best_name, round(best_score * 100, 1), best_axes, best_tag

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
        # ネストされた辞書かどうかの判定（マルチポジション形式かフラット形式か）
        is_multi = any(isinstance(v, dict) for v in positions_data.values())
        
        if is_multi:
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
        else:
            # フラットな形式（テスト等）
            putouts = positions_data.get('putouts') or positions_data.get('put_outs') or 0
            assists = positions_data.get('assists') or 0
            # イニング数があれば試合数に換算
            games = positions_data.get('games') or (positions_data.get('innings', 0) / 9) or 1
            rf = (putouts + assists) / games
            defense_score = (rf / 2.0) * 50 + 25 # デフォルト外野手
    
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
    speed: float = 50.0,
    **kwargs
) -> float:
    """
    現在の実績を0〜100のスコアに変換する。
    1軍実績がない場合、2軍（ファーム）実績を割り引いて加味する。
    """
    # テストコードからの引数名対応
    if 'defense_stats' in kwargs and positions_data is None:
        positions_data = kwargs['defense_stats']
    if 'speed_stats' in kwargs:
        s_stats = kwargs['speed_stats']
        if isinstance(s_stats, dict):
            speed = 50 + (s_stats.get('stolen_bases', 0) * 2) + (s_stats.get('triples', 0) * 5)
            if 'success_rate' in s_stats:
                speed *= s_stats['success_rate']

    # 2軍実績の統合
    if batting_avg is None and farm_stats:
        batting_avg = farm_stats.get('avg', 0.0) * 0.8
        home_runs = farm_stats.get('hr', 0) * 0.7
    
    sub = calculate_subscores(positions_data, batting_avg, home_runs, era, speed)
    defense = sub['defense']
    speed = sub['speed']

    score = 50.0
    
    if batting_avg is not None and (batting_avg > 0 or (home_runs or 0) > 0):
        avg_score = ((max(0.150, min(0.350, batting_avg)) - 0.150) / (0.350 - 0.150)) * 100
        hr_score = (min(home_runs or 0, 40) / 40.0) * 100
        score = (avg_score * 0.30) + (hr_score * 0.20) + (defense * 0.35) + (speed * 0.15)
        
    elif era is not None and era > 0:
        era_clamped = max(1.20, min(7.00, era))
        era_score = 100 - ((era_clamped - 1.20) / (7.00 - 1.20)) * 100
        score = (era_score * 0.8) + (defense * 0.15) + (speed * 0.05)
        
    # サンプル数による信頼度補正 (Phase 2)
    # 実績が少ない選手はスコアをベースライン(25.0)に引き寄せる
    pa = kwargs.get('plate_appearances', 0)
    ip = kwargs.get('innings_pitched', 0)
    team_games = kwargs.get('team_games', 20) # まだ序盤なのでデフォルト20程度
    
    if batting_avg is not None:
        target_pa = team_games * 2.0 # チーム試合数×2打席程度あれば信頼
        weight = min(1.0, pa / target_pa) if target_pa > 0 else 0
        score = score * weight + 25.0 * (1.0 - weight)
    elif era is not None:
        target_ip = team_games * 0.5 # チーム試合数×0.5イニング程度あれば信頼
        weight = min(1.0, ip / target_ip) if target_ip > 0 else 0
        score = score * weight + 25.0 * (1.0 - weight)

    return max(0.0, min(100.0, score))

def calculate_potential(age, years_in_pro, current_performance, position="内野手", situational_data=None, **kwargs):
    """
    選手の総合的なポテンシャルスコアを算出。
    ポジション別エイジングカーブとシチュエーション補正（覚醒）を考慮。
    """
    # 基本のポテンシャル計算
    # 若いほど、プロ年数が短いほど伸び代が大きい
    growth_factor = 1.0 / (1.0 + (age - 18) * 0.15 + years_in_pro * 0.05)
    potential = current_performance + (100 - current_performance) * growth_factor
    
    # ポジション別補正（エイジングカーブの模倣）
    if position == "捕手":
        # 捕手は息が長く、ベテランでも経験値によるプラスがある
        potential += max(0, (age - 30) * 0.5)
    elif position == "外野手" and kwargs.get('speed_score', 50) > 80:
        # 俊足外野手は衰えが早い傾向
        potential -= max(0, (age - 32) * 1.5)
    
    # シチュエーション補正（覚醒機能）
    if situational_data:
        if situational_data.get('is_clutch'):
            # 勝負強さボーナス
            potential += 8.0
        if situational_data.get('breakout_phase'):
            # ブレイクアウト中
            potential += 12.0

    return max(0.0, min(100.0, potential))

def calculate_potential_score(age, years_in_pro, current_performance, **kwargs):
    """互換性のためのラッパー"""
    return calculate_potential(age, years_in_pro, current_performance, **kwargs)

import random

def calculate_potential_bounds(pot_axes, age):
    """
    モンテカルロ・シミュレーションにより、ポテンシャルの上限・下限（±1σ）を算出する。
    若手（ageが小さい）ほどブレ幅（標準偏差）が大きくなる。
    """
    if not pot_axes or len(pot_axes) != 5:
        return [0]*5, [0]*5
        
    SIMULATIONS = 100
    base_std_dev = max(2.0, (35 - age) * 0.8) # 18歳なら13.6、30歳なら4.0の標準偏差
    
    # 軸ごとにシミュレーション結果を格納
    results = [[] for _ in range(5)]
    
    for _ in range(SIMULATIONS):
        for i in range(5):
            # 成長の期待値に正規分布でノイズを加える
            noise = random.gauss(0, base_std_dev)
            val = pot_axes[i] + noise
            results[i].append(max(0, min(100, val)))
            
    upper_bounds = []
    lower_bounds = []
    for i in range(5):
        mean = sum(results[i]) / SIMULATIONS
        variance = sum((x - mean) ** 2 for x in results[i]) / SIMULATIONS
        std_dev = math.sqrt(variance)
        upper_bounds.append(int(min(100, mean + std_dev)))
        lower_bounds.append(int(max(0, mean - std_dev)))
        
    return upper_bounds, lower_bounds
