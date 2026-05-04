import requests
from bs4 import BeautifulSoup

def debug_utf8():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    # 完全にUTF-8として扱う
    content = res.content.decode('utf-8', errors='ignore')
    soup = BeautifulSoup(content, 'html.parser')
    
    with open('debug_utf8.txt', 'w', encoding='utf-8') as f:
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'caption', 'div', 'tr']):
            text = elem.text.strip()
            if any(p in text for p in ["投手", "捕手", "一塁手", "二塁手", "三塁手", "遊撃手", "外野手"]):
                f.write(f"Match: <{elem.name}>: {text}\n")

if __name__ == "__main__":
    debug_utf8()
