import requests
from bs4 import BeautifulSoup

def find_sakakura_position():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    rows = soup.find_all('tr')
    for r in rows:
        if '坂倉' in r.text:
            # テーブルの見出しを探す（caption, h3, h4, または前のセクション）
            # NPBのチーム別守備成績ページは、各ポジションが別々のテーブルになっている
            table = r.find_parent('table')
            title = ""
            if table:
                # 前の要素を探索
                prev = table.find_previous(['h1', 'h2', 'h3', 'h4', 'caption', 'div'])
                title = prev.text.strip() if prev else "Unknown"
            
            print(f"Position Category: {title}")
            print(f"Row data: {r.text.strip().split()}")

if __name__ == "__main__":
    find_sakakura_position()
