import requests
from bs4 import BeautifulSoup
import re

def safe_int(val):
    try:
        v = val.strip().replace('-', '').replace('ー', '')
        return int(v) if v else None
    except: return None

def scrape_test(team_code):
    url = f'https://npb.jp/bis/2026/stats/idb1_{team_code}.html'
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    # Detect encoding
    if res.encoding == 'ISO-8859-1':
        res.encoding = res.apparent_encoding
    
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table')
    if not table:
        print("No table")
        return
        
    rows = table.find_all('tr')
    # Get headers from the first tr that has ths
    header_row = None
    for row in rows:
        if row.find('th'):
            header_row = row
            break
            
    if not header_row:
        print("No header row")
        return
        
    headers_text = [th.text.strip() for th in header_row.find_all('th')]
    print("Detected Headers:", headers_text)
    
    # Check if '試合' and '打席' are in headers
    if '試合' not in headers_text:
        print("Warning: '試合' not in headers")
    if '打席' not in headers_text:
        print("Warning: '打席' not in headers")
        
    max_games = 0
    players = []
    for row in rows:
        tds = row.find_all('td')
        if len(tds) < 5: continue
        
        # Mapping columns
        def get_val(key):
            if key in headers_text:
                idx = headers_text.index(key)
                # Note: header_row might have 24 ths, but data row might have 24 tds.
                # However, sometimes '選手' is a th in the data row too.
                # Let's get all cells in the row.
                cells = row.find_all(['td', 'th'])
                return cells[idx].text.strip() if idx < len(cells) else ''
            return ''
            
        name = get_val('選手')
        games = safe_int(get_val('試合')) or 0
        pa = safe_int(get_val('打席'))
        
        if games > max_games: max_games = games
        players.append({'name': name, 'games': games, 'pa': pa})
        
    print(f"Scraped {len(players)} players. Max games: {max_games}")
    for p in players[:5]:
        print(p)

if __name__ == "__main__":
    scrape_test('c')
