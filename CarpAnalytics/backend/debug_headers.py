import requests
from bs4 import BeautifulSoup

def debug_headers():
    url = "https://npb.jp/bis/2026/stats/idb1_c.html"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.find('table')
    ths = table.find_all('th')
    for th in ths:
        txt = th.text.strip()
        print(f"Header: '{txt}' (repr: {repr(txt)})")

if __name__ == "__main__":
    debug_headers()
