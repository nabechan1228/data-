import requests
from bs4 import BeautifulSoup

url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
res = requests.get(url)
res.encoding = 'shift_jis'
soup = BeautifulSoup(res.text, 'html.parser')

with open('h4_output.txt', 'w', encoding='utf-8') as f:
    f.write(f"Encoding used: {res.encoding}\n")
    for h4 in soup.find_all('h4'):
        f.write(f"h4: '{h4.text.strip()}' class: {h4.get('class')}\n")
