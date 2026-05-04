import requests
from bs4 import BeautifulSoup

def deep_debug():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    res.encoding = 'shift_jis'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # 全ての要素を順に走査し、テーブル付近のテキストを確認
    for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'div', 'table']):
        if elem.name == 'table':
            print(f"--- TABLE FOUND ---")
        else:
            text = elem.text.strip()
            if any(p in text for p in ["投手", "捕手", "一塁手", "二塁手", "三塁手", "遊撃手", "外野手"]):
                print(f"Header candidate: <{elem.name} class='{elem.get('class')}'>: {text}")

if __name__ == "__main__":
    deep_debug()
