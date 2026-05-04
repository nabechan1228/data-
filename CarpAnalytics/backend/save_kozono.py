import requests
url = 'https://npb.jp/bis/players/01705138.html'
res = requests.get(url)
res.encoding = 'utf-8'
with open('kozono_detail.html', 'w', encoding='utf-8') as f:
    f.write(res.text)
