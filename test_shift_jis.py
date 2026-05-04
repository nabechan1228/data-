import requests
from bs4 import BeautifulSoup

def test_shift_jis():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    res.encoding = 'shift_jis'
    soup = BeautifulSoup(res.text, 'html.parser')
    
    print("--- h3 ---")
    for h3 in soup.find_all('h3'):
        print(f"h3: {h3.text.strip()}")
    
    print("--- div stats_title ---")
    for div in soup.find_all('div', class_='stats_title'):
        print(f"div: {div.text.strip()}")

if __name__ == "__main__":
    test_shift_jis()
