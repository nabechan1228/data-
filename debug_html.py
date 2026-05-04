import requests
from bs4 import BeautifulSoup

def debug_html():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    res.encoding = 'shift_jis'
    soup = BeautifulSoup(res.text, 'html.parser')
    tables = soup.find_all('table')
    print(f"Tables count: {len(tables)}")
    if tables:
        print(f"First table headers: {[th.text.strip() for th in tables[0].find_all('th')]}")

if __name__ == "__main__":
    debug_html()
