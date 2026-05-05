import sqlite3
import random
import os
from datetime import datetime, timedelta

# backendディレクトリをパスに追加
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import history_engine

def insert_mock_history():
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'carp_data.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 小園海斗(野手)と床田寛樹(投手)でテスト
    batters = ['小園海斗', '秋山翔吾']
    pitchers = ['床田寛樹']
    
    today = datetime.now()
    
    for player_name in batters:
        # 小園は急成長、秋山は平坦
        for i in range(30):
            if player_name == '小園海斗':
                ops = random.uniform(0.500, 0.600) if i >= 14 else random.uniform(0.800, 0.900)
            else:
                ops = random.uniform(0.700, 0.750)
                
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute('''
                INSERT OR REPLACE INTO player_daily_snapshots
                (snapshot_date, player_name, team, ops, k9, similarity_name, similarity_score, is_breaking_out)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date_str, player_name, '広島東洋カープ', ops, None, 'Test', 80.0, False
            ))
            
    for player_name in pitchers:
        for i in range(30):
            # 床田はK/9が急成長
            k9 = random.uniform(4.0, 5.0) if i >= 14 else random.uniform(8.0, 9.0)
            
            date_str = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            cursor.execute('''
                INSERT OR REPLACE INTO player_daily_snapshots
                (snapshot_date, player_name, team, ops, k9, similarity_name, similarity_score, is_breaking_out)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date_str, player_name, '広島東洋カープ', None, k9, 'Test', 80.0, False
            ))
            
    # まずplayersテーブルのフラグをリセット
    cursor.execute('UPDATE players SET is_breaking_out = 0')
            
    conn.commit()
    conn.close()
    
    print("Mock data inserted. Running evaluation...")
    history_engine.evaluate_trends()
    
    # 結果の確認
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT name, is_breaking_out FROM players WHERE is_breaking_out = 1')
    breakouts = cursor.fetchall()
    print("Breakouts detected:", breakouts)
    conn.close()

if __name__ == '__main__':
    insert_mock_history()
