import requests
from bs4 import BeautifulSoup

def debug_to_file():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    res.encoding = 'shift_jis'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'caption', 'div', 'table']):
            if elem.name == 'table':
                f.write("--- TABLE ---\n")
            else:
                text = elem.text.strip()
                if any(p in text for p in ["投手", "捕手", "一塁手", "二塁手", "三塁手", "遊撃手", "外野手"]):
                    f.write(f"Match: <{elem.name}>: {text}\n")

if __name__ == "__main__":
    debug_to_file()
