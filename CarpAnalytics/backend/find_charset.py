import requests

url = 'https://npb.jp/bis/2026/stats/idf1_c.html'
res = requests.get(url)
content_str = res.content.decode('ascii', errors='ignore')
if 'charset' in content_str:
    idx = content_str.find('charset')
    print(f"Charset info: {content_str[idx:idx+50]}")
