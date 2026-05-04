import requests
from bs4 import BeautifulSoup

url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
res = requests.get(url)
res.encoding = 'shift_jis'
soup = BeautifulSoup(res.text, 'html.parser')

print(f"Encoding used: {res.encoding}")
for h4 in soup.find_all('h4'):
    print(f"h4: '{h4.text.strip()}' class: {h4.get('class')}")
