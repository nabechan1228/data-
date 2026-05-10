import requests
try:
    res = requests.get('http://127.0.0.1:8001/api/players', timeout=5)
    data = res.json()
    print(f"Status: {data.get('status')}")
    players = data.get('data', [])
    print(f"Count: {len(players)}")
    if players:
        print(f"First Player Name: {players[0].get('name')}")
        print(f"First Player Team: {players[0].get('team')}")
except Exception as e:
    print(f"Error: {e}")
