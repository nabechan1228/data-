import requests
from bs4 import BeautifulSoup

def check_all_texts():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    # 実際はUTF-8のようなので、デフォルト（UTF-8）でパース
    soup = BeautifulSoup(res.content, 'html.parser')
    
    for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'caption', 'div']):
        text = elem.text.strip()
        if any(p in text for p in ["投手", "捕手", "一塁手", "二塁手", "三塁手", "遊撃手", "外野手"]):
            print(f"Match: <{elem.name} class='{elem.get('class')}'>: {text}")

if __name__ == "__main__":
    check_all_texts()
