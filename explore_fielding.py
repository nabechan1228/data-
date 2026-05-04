import requests
from bs4 import BeautifulSoup
import re

def explore_fielding():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # ページ内のすべてのテキスト要素を調べる
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'div', 'caption']):
        text = tag.text.strip()
        if any(p in text for p in ['投手', '捕手', '一塁手', '二塁手', '三塁手', '遊撃手', '外野手']):
            print(f"Tag: {tag.name}, Text: {text}")
            # その直後のテーブルを確認
            nxt = tag.find_next('table')
            if nxt:
                print(f"  -> Followed by table with {len(nxt.find_all('tr'))} rows")

if __name__ == "__main__":
    explore_fielding()
