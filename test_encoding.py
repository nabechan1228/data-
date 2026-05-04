import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'CarpAnalytics', 'backend'))
import requests
from bs4 import BeautifulSoup

def test_encoding():
    url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
    res = requests.get(url)
    print(f"Original encoding: {res.encoding}")
    
    # Try UTF-8
    res.encoding = 'utf-8'
    soup = BeautifulSoup(res.text, 'html.parser')
    h3 = soup.find('h3')
    print(f"UTF-8: {h3.text if h3 else 'None'}")
    
    # Try Shift-JIS
    res.encoding = 'shift_jis'
    soup = BeautifulSoup(res.text, 'html.parser')
    h3 = soup.find('h3')
    print(f"Shift-JIS: {h3.text if h3 else 'None'}")

if __name__ == "__main__":
    test_encoding()
