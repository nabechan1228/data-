import requests
from bs4 import BeautifulSoup

def check_bytes():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    
    for h3 in soup.find_all('h3'):
        print(f"h3 bytes: {h3.text.strip().encode('utf-8', errors='ignore')}")
    
    for div in soup.find_all('div', class_='stats_title'):
        print(f"div bytes: {div.text.strip().encode('utf-8', errors='ignore')}")

if __name__ == "__main__":
    check_bytes()
