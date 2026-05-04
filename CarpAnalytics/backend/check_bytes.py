import requests

url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
res = requests.get(url)
print(f"res.content[:200]: {res.content[:200]}")
