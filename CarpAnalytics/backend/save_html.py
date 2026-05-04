import requests
url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
res = requests.get(url)
with open('idf1_c.html', 'wb') as f:
    f.write(res.content)
