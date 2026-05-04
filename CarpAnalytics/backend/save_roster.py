import requests
url = 'https://npb.jp/bis/teams/rst_c.html'
res = requests.get(url)
res.encoding = 'utf-8'
with open('rst_c.html', 'w', encoding='utf-8') as f:
    f.write(res.text)
