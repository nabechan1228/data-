import math

def calculate_chart_area(values: list) -> float:
    """レーダーチャートの各項目の値から多角形の面積を計算する"""
    n = len(values)
    if n < 3: return 0.0
    area = 0.0
    # 正多角形の各頂点間の三角形の面積を合計
    # Area = 0.5 * sum(r_i * r_{i+1} * sin(2*pi/n))
    sin_theta = math.sin(2 * math.pi / n)
    for i in range(n):
        r1 = values[i]
        r2 = values[(i + 1) % n]
        area += 0.5 * r1 * r2 * sin_theta
    return area

def calculate_potential(
    age: int, 
    years_in_pro: int, 
    current_performance: float, 
    position: str,
    speed_score: float = 50.0,
    situational_data: dict = None
) -> float:
    """
    選手のポテンシャルを年齢・プロ年数・現在実績・ポジションから計算する。
    """
    # 基準点は現在実績をベースにする（実績がある程度ある選手は底上げされる）
    base_potential = current_performance * 0.6 + 30.0
    
    # --- 1. 年齢による加齢曲線（ポジション特性を反映） ---
    # 捕手は経験重視のため衰えが遅い、スピードスターは衰えが早い
    is_catcher = '捕手' in position
    is_speedster = speed_score > 80
    
    peak_start = 24
    decline_start = 32
    
    if is_catcher:
        decline_start = 34  # 捕手は34歳まで維持
    elif is_speedster:
        decline_start = 30  # スピード型は30歳から低下開始
        
    if age < peak_start:
        base_potential += (peak_start - age) * 3.5
    elif age > decline_start:
        penalty = (age - decline_start) * 2.5
        
        # 実績があるレジェンド級選手への配慮（実績80以上なら減衰を50%軽減）
        if current_performance > 80:
            penalty *= 0.5
        elif current_performance > 70:
            penalty *= 0.75
            
        if is_catcher:
            penalty *= 0.6  # 捕手はさらに減衰が緩やか
        elif is_speedster:
            penalty *= 1.5  # スピード型は減衰が急激
            
        base_potential -= penalty
        
    # 下限値の保証（実績があるレジェンドが極端に低く出ないようにする）
    min_potential = current_performance * 0.8
    base_potential = max(base_potential, min_potential)
        
    # --- 2. プロ年数に対する実績の早熟度 ---
    if years_in_pro < 3 and current_performance > 60:
        base_potential += 10.0
        
    # --- 3. ポジションによる希少価値 ---
    pos_bonus = 0.0
    if is_catcher or '遊撃手' in position:
        pos_bonus = 5.0
    elif '二塁手' in position or '中堅手' in position:
        pos_bonus = 3.0
    base_potential += pos_bonus

    base_potential += pos_bonus

    # --- 4. 局地戦ボーナス (Situational Bonus) ---
    if situational_data:
        if situational_data.get('is_clutch'):
            base_potential += 3.0  # 得点圏での強さ
        if situational_data.get('early_count_aggressiveness', 0) > 0.5:
            base_potential += 2.0  # 初球積極性

    # --- 5. 面積・収束率の計算用データの付与 ---
    # ここでは便宜上、ベースとなるポテンシャル値を返す
    return max(0.0, min(100.0, base_potential))

def calculate_subscores(
    batting_avg: float = None, 
    home_runs: int = None, 
    era: float = None,
    defense_stats: dict = None, # {"put_outs": 100, "assists": 50, "innings": 800, "pos": "SS"}
    speed_stats: dict = None,
    defense: float = 50.0,
    speed: float = 50.0
) -> dict:
    """守備力・走力などの個別スコアを算出する"""
    # ポジション別平均RF（NPB目安）
    RF_AVG = {
        '1B': 9.0, '2B': 4.8, '3B': 2.7, 'SS': 4.8,
        'OF': 2.1, 'C': 8.5, 'P': 1.2, 'default': 4.0
    }
    # 1. 走力スコアの客観的算出
    if speed_stats:
        sb = speed_stats.get('stolen_bases', 0)
        triples = speed_stats.get('triples', 0)
        rate = speed_stats.get('success_rate', 0.0)
        # ハイブリッド計算: (盗塁*2) + (三塁打*5) + (成功率*20)
        calc_speed = (sb * 2) + (triples * 5) + (rate * 20)
        speed = max(30.0, min(95.0, calc_speed))
        
    # 2. 守備スコアの客観的算出 (Range Factor)
    if defense_stats:
        po = defense_stats.get('put_outs') or 0
        asst = defense_stats.get('assists') or 0
        innings = defense_stats.get('innings') or 0
        if (not innings or innings <= 0) and defense_stats.get('games', 0) > 0:
            innings = defense_stats.get('games') * 6.0

        if innings > 0:
            rf = (po + asst) / innings * 9
            
            # ポジション別正規化: (RF / RF_avg) * 50 + 25
            pos = defense_stats.get('pos', 'default')
            # "内野手(二塁)" のような文字列からキーを抽出
            pos_key = 'default'
            if '一塁' in pos: pos_key = '1B'
            elif '二塁' in pos: pos_key = '2B'
            elif '三塁' in pos: pos_key = '3B'
            elif '遊撃' in pos: pos_key = 'SS'
            elif '外野' in pos: pos_key = 'OF'
            elif '捕手' in pos: pos_key = 'C'
            elif '投手' in pos: pos_key = 'P'
            
            avg_rf = RF_AVG.get(pos_key, RF_AVG['default'])
            defense_score = (rf / avg_rf) * 50 + 25
            defense = max(30.0, min(99.0, defense_score))

    return {"defense": defense, "speed": speed}

def calculate_current_performance(
    batting_avg: float = None, 
    home_runs: int = None, 
    era: float = None,
    # 詳細スタッツ（客観的算出用）
    defense_stats: dict = None, 
    speed_stats: dict = None,
    # 二軍実績（一軍実績がない場合の補完）
    farm_stats: dict = None, # {"avg": 0.280, "hr": 5}
    # 従来互換用の固定値
    defense: float = 50.0,
    speed: float = 50.0
) -> float:
    """
    現在の実績を0〜100のスコアに変換する。守備力・走力も加味。
    """
    # 1. 二軍実績のシームレスな統合（一軍打率がない場合）
    if batting_avg is None and farm_stats:
        # 二軍成績を割り引いて計算に回す
        batting_avg = farm_stats.get('avg', 0.0) * 0.8
        home_runs = farm_stats.get('hr', 0) * 0.7
    
    sub = calculate_subscores(batting_avg, home_runs, era, defense_stats, speed_stats, defense, speed)
    defense = sub['defense']
    speed = sub['speed']

    score = 50.0
    
    # 野手の場合
    if batting_avg is not None and (batting_avg > 0 or home_runs > 0):
        avg_score = ((max(0.150, min(0.350, batting_avg)) - 0.150) / (0.350 - 0.150)) * 100
        hr_score = (min(home_runs or 0, 40) / 40.0) * 100
        # 打撃(50%)、守備(35%)、走力(15%)
        score = (avg_score * 0.30) + (hr_score * 0.20) + (defense * 0.35) + (speed * 0.15)
        
    # 投手の場合
    elif era is not None and era > 0:
        era_clamped = max(1.20, min(7.00, era))
        era_score = 100 - ((era_clamped - 1.20) / (7.00 - 1.20)) * 100
        score = (era_score * 0.8) + (defense * 0.15) + (speed * 0.05)
        
    return max(0.0, min(100.0, score))
