import database
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def record_daily_snapshots():
    """現在のplayersデータからスナップショットを作成し保存する"""
    players = database.get_all_players()
    snapshots = []
    today = datetime.now().strftime("%Y-%m-%d")
    
    for p in players:
        stats = database.get_player_season_stats(p['name'])
        batting = next((s for s in stats if s['stat_type'] == 'batting'), None)
        pitching = next((s for s in stats if s['stat_type'] == 'pitching'), None)
        
        ops = batting.get('ops') if batting else None
        
        k9 = None
        if pitching:
            ip = pitching.get('innings_pitched', 0)
            so = pitching.get('strikeouts', 0)
            k9 = (so * 9 / ip) if ip > 0 else 0

        snapshots.append({
            'snapshot_date': today,
            'player_name': p['name'],
            'team': p['team'],
            'ops': ops,
            'k9': k9,
            'similarity_name': p.get('similarity_name'),
            'similarity_score': p.get('similarity_score'),
            'is_breaking_out': p.get('is_breaking_out')
        })
        
    database.save_daily_snapshots(snapshots)
    logger.info(f"Recorded {len(snapshots)} daily snapshots for {today}.")

def evaluate_trends():
    """過去30日と直近14日の成績トレンドを比較し、覚醒の兆し（is_breaking_out）を自動判定する"""
    players = database.get_all_players()
    updated_count = 0
    
    for p in players:
        # 既にis_breaking_outがTrueならそのまま（もしくはロジックで落とすことも可能）
        # 今回はFalseの選手について、急激な伸びを検出してTrueにする
        if p.get('is_breaking_out'):
            continue
            
        snapshots = database.get_player_snapshots(p['name'], days=30)
        if len(snapshots) < 14:
            continue # データ不足
            
        # 投手か野手か判定
        is_pitcher = p['position'] == '投手' or p.get('era') is not None
        
        recent_14 = snapshots[:14]
        older_16 = snapshots[14:] # 15〜30日前のデータ
        
        if not older_16:
            continue
            
        breaking_out = False
        
        if is_pitcher:
            # 奪三振率（K/9）の向上をチェック
            recent_k9 = [s['k9'] for s in recent_14 if s['k9'] is not None]
            older_k9 = [s['k9'] for s in older_16 if s['k9'] is not None]
            
            if recent_k9 and older_k9:
                avg_recent_k9 = sum(recent_k9) / len(recent_k9)
                avg_older_k9 = sum(older_k9) / len(older_k9)
                
                # 古いK/9が低く、最近のK/9が20%以上向上し、かつ7.0を超えている場合
                if avg_older_k9 > 0 and (avg_recent_k9 - avg_older_k9) / avg_older_k9 > 0.20 and avg_recent_k9 > 7.0:
                    breaking_out = True
        else:
            # 野手はOPSの向上をチェック
            recent_ops = [s['ops'] for s in recent_14 if s['ops'] is not None]
            older_ops = [s['ops'] for s in older_16 if s['ops'] is not None]
            
            if recent_ops and older_ops:
                avg_recent_ops = sum(recent_ops) / len(recent_ops)
                avg_older_ops = sum(older_ops) / len(older_ops)
                
                # OPSが15%以上向上し、かつ0.750を超えている場合
                if avg_older_ops > 0 and (avg_recent_ops - avg_older_ops) / avg_older_ops > 0.15 and avg_recent_ops > 0.750:
                    breaking_out = True
                    
        if breaking_out:
            logger.info(f"Breakout detected for {p['name']}!")
            database.update_player_breaking_out(p['name'], True)
            updated_count += 1
            
    return updated_count

def run_daily_history_pipeline():
    record_daily_snapshots()
    count = evaluate_trends()
    logger.info(f"Trend evaluation complete. Detected {count} new breakouts.")
