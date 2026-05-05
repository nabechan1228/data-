import sys
import os
import json

# backendディレクトリをパスに追加
sys.path.append(os.path.join(os.getcwd(), 'CarpAnalytics', 'backend'))

import lineup_engine

db_path = 'CarpAnalytics/backend/carp_data.db'
team_name = '広島東洋カープ'

try:
    result = lineup_engine.get_optimized_team_data(team_name, db_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
except Exception as e:
    import traceback
    traceback.print_exc()
