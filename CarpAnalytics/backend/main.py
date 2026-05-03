from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import database

app = FastAPI(title="Carp Insight Pro API")

# フロントエンドからのアクセスを許可
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/players")
def get_players():
    """全選手のデータを取得する"""
    players = database.get_all_players()
    return {"status": "success", "data": players}

@app.get("/api/players/{player_id}")
def get_player(player_id: int):
    """特定選手のデータを取得する"""
    players = database.get_all_players()
    player = next((p for p in players if p["id"] == player_id), None)
    if player:
        return {"status": "success", "data": player}
    return {"status": "error", "message": "Player not found"}
