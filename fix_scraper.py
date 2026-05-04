import os

def fix_scraper():
    path = os.path.join('CarpAnalytics', 'backend', 'stats_scraper.py')
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 複数箇所あるので置換
    new_content = content.replace("'player_name': player_name,", "'player_name': normalize_name(player_name),")
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed stats_scraper.py")

if __name__ == "__main__":
    fix_scraper()
