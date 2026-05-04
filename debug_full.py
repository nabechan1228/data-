import requests
from bs4 import BeautifulSoup

def debug_full():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    # apparent_encodingを使ってみる
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, 'html.parser')
    
    with open('debug_full.txt', 'w', encoding='utf-8') as f:
        f.write(f"Encoding: {res.encoding}\n")
        for elem in soup.find_all(['h1', 'h2', 'h3', 'h4', 'caption', 'div', 'tr']):
            text = elem.text.strip()
            if text:
                f.write(f"<{elem.name}>: {text[:50]}\n")

if __name__ == "__main__":
    debug_full()
