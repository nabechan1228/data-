import requests
url = 'https://npb.jp/bis/players/search/result?search_keyword=%E5%B0%8F%E5%9C%92%E6%B5%B7%E6%96%97'
res = requests.get(url)
res.encoding = 'utf-8'
with open('search_kozono.html', 'w', encoding='utf-8') as f:
    f.write(res.text)
