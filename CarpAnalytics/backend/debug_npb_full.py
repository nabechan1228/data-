import requests
from bs4 import BeautifulSoup

def debug_npb_full():
    url = "https://npb.jp/bis/2026/stats/idb1_c.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table')
    if not table:
        print("No table")
        return
        
    rows = table.find_all('tr')
    print(f"Total rows: {len(rows)}")
    
    # Print headers
    head_row = rows[0]
    ths = head_row.find_all(['th', 'td'])
    print("Header Row:", [th.text.strip() for th in ths])
    
    # Print last 3 rows
    for i in range(max(0, len(rows)-3), len(rows)):
        cells = rows[i].find_all(['td', 'th'])
        print(f"Row {i}:", [c.text.strip() for c in cells])

if __name__ == "__main__":
    debug_npb_full()
