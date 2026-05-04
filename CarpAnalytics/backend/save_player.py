import requests
url = 'https://npb.jp/bis/players/51955152.html'
res = requests.get(url)
res.encoding = 'utf-8'
with open('player_detail.html', 'w', encoding='utf-8') as f:
    f.write(res.text)
