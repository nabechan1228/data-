import json
import database
import potential_engine

def scrape_mock_data():
    """
    実際のウェブスクレイピングの代わりに、テスト用のカープ選手モックデータを生成します。
    ※本番環境ではBeautifulSoup等を用いてNPB/Yahooサイトからスクレイピングします。
    """
    mock_players = [
        {
            "name": "坂倉 将吾",
            "position": "捕手",
            "age": 25,
            "years_in_pro": 8,
            "batting_avg": 0.285,
            "home_runs": 12,
            "era": None,
            "image_url": "https://placehold.co/150x150/FF0000/FFFFFF?text=Sakakura"
        },
        {
            "name": "堂林 翔太",
            "position": "内野手",
            "age": 32,
            "years_in_pro": 15,
            "batting_avg": 0.260,
            "home_runs": 8,
            "era": None,
            "image_url": "https://placehold.co/150x150/FF0000/FFFFFF?text=Dobayashi"
        },
        {
            "name": "栗林 良吏",
            "position": "投手",
            "age": 27,
            "years_in_pro": 4,
            "batting_avg": None,
            "home_runs": None,
            "era": 1.55,
            "image_url": "https://placehold.co/150x150/FF0000/FFFFFF?text=Kuribayashi"
        },
        {
            "name": "田村 俊介",
            "position": "外野手",
            "age": 20,
            "years_in_pro": 3,
            "batting_avg": 0.220,
            "home_runs": 2,
            "era": None,
            "image_url": "https://placehold.co/150x150/FF0000/FFFFFF?text=Tamura"
        },
        {
            "name": "床田 寛樹",
            "position": "投手",
            "age": 29,
            "years_in_pro": 8,
            "batting_avg": None,
            "home_runs": None,
            "era": 2.15,
            "image_url": "https://placehold.co/150x150/FF0000/FFFFFF?text=Tokoda"
        }
    ]

    # ポテンシャルと実績スコアを計算して付与
    for p in mock_players:
        p['current_performance'] = potential_engine.calculate_current_performance(p['batting_avg'], p['home_runs'], p['era'])
        p['potential_score'] = potential_engine.calculate_potential(p['age'], p['years_in_pro'], p['current_performance'], p['position'])

    return mock_players

def main():
    database.init_db()
    players = scrape_mock_data()
    database.save_players(players)
    print(f"Successfully scraped and saved {len(players)} players to the database.")

if __name__ == "__main__":
    main()
