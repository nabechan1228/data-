import requests
from bs4 import BeautifulSoup

def debug_npb_table():
    url = "https://npb.jp/bis/2026/stats/idb1_c.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    if not tables:
        print("No tables found")
        return
    
    table = tables[0]
    ths = table.find_all('th')
    print("Headers:", [th.text.strip() for th in ths])
    
    rows = table.find_all('tr')
    for i, row in enumerate(rows[:5]):
        cells = row.find_all(['td', 'th'])
        print(f"Row {i}:", [c.text.strip() for c in cells])

if __name__ == "__main__":
    debug_npb_table()
