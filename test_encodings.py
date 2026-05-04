import requests
from bs4 import BeautifulSoup

def test_encodings():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    
    encodings = ['shift_jis', 'utf-8', 'euc-jp', 'cp932']
    for enc in encodings:
        print(f"--- Testing {enc} ---")
        try:
            text = res.content.decode(enc, errors='ignore')
            soup = BeautifulSoup(text, 'html.parser')
            h3 = soup.find('h3')
            if h3:
                print(f"h3 text: {h3.text.strip()}")
            else:
                # div with class stats_title
                div = soup.find('div', class_='stats_title')
                print(f"div stats_title: {div.text.strip() if div else 'None'}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_encodings()
