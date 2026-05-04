import requests
url = 'https://npb.jp/bis/2026/stats/idb1_c.html'
res = requests.get(url)
res.encoding = 'utf-8'
with open('idb1_c.html', 'w', encoding='utf-8') as f:
    f.write(res.text)
