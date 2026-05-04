import requests


urls = [
    'https://npb.jp/bis/teams/rst_c.html',
    'https://npb.jp/bis/2026/stats/idb1_c.html'
]

for url in urls:
    res = requests.get(url)
    print(f"URL: {url}")
    print(f"res.encoding: {res.encoding}")
    print(f"res.apparent_encoding: {res.apparent_encoding}")
    print(f"Content snippet: {res.content[:200]}")
    # Search for charset in content
    content_lower = res.content.lower()
    if b'charset=utf-8' in content_lower: print("Found: charset=utf-8")
    if b'charset=shift_jis' in content_lower: print("Found: charset=shift_jis")
    if b'charset=cp932' in content_lower: print("Found: charset=cp932")
    print("-" * 20)
