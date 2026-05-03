from fastapi import FastAPI, Request, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv
import database
import subprocess
import os
import logging

load_dotenv()

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# レート制限（IPアドレスベース）
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="NPB Insight Pro API",
    docs_url=None,      # Swagger UIを本番公開しない（セキュリティ対策）
    redoc_url=None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 許可するオリジンを.envから取得
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],   # 必要なメソッドのみ
    allow_headers=["Content-Type", "X-Request-Token"],
)

# ─────────────────────────────────────
# セキュリティヘッダーミドルウェア
# ─────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    return response

# ─────────────────────────────────────
# グローバルエラーハンドラー（詳細情報の隠蔽）
# ─────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "サーバー内部エラーが発生しました。"},
    )

# ─────────────────────────────────────
# 依存性：シークレットトークン検証
# ─────────────────────────────────────
SECRET_TOKEN = os.getenv("SCRAPE_SECRET_TOKEN", "")

def verify_token(x_request_token: str = Header(...)):
    if not SECRET_TOKEN or x_request_token != SECRET_TOKEN:
        logger.warning("Unauthorized scrape attempt blocked.")
        raise HTTPException(status_code=401, detail="認証トークンが無効です。")

# ─────────────────────────────────────
# エンドポイント
# ─────────────────────────────────────

@app.get("/api/players")
@limiter.limit("30/minute")
def get_players(request: Request):
    """全選手データを取得する（1分間に30回まで）"""
    try:
        players = database.get_all_players()
        logger.info(f"GET /api/players -> {len(players)} players returned.")
        return {"status": "success", "data": players}
    except Exception as e:
        logger.error(f"DB error in get_players: {e}")
        raise HTTPException(status_code=500, detail="データ取得中にエラーが発生しました。")


@app.get("/api/players/{player_id}")
@limiter.limit("30/minute")
def get_player(player_id: int, request: Request):
    """特定選手のデータを取得する"""
    # 入力バリデーション
    if player_id <= 0 or player_id > 10000:
        raise HTTPException(status_code=400, detail="無効な選手IDです。")
    try:
        players = database.get_all_players()
        player = next((p for p in players if p["id"] == player_id), None)
        if player:
            logger.info(f"GET /api/players/{player_id} -> found.")
            return {"status": "success", "data": player}
        raise HTTPException(status_code=404, detail="選手が見つかりません。")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DB error in get_player: {e}")
        raise HTTPException(status_code=500, detail="データ取得中にエラーが発生しました。")


@app.post("/api/update-data")
@limiter.limit("3/hour")
def update_data(request: Request, _: None = Depends(verify_token)):
    """
    スクレイピングを再実行してDBを更新する（要シークレットトークン・1時間に3回まで）
    """
    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        scraper_path = os.path.join(backend_dir, "scraper.py")
        python_exec = os.path.join(backend_dir, "..", "venv", "Scripts", "python.exe")
        python_exec = os.path.abspath(python_exec)
        
        logger.info("Data update triggered via API.")
        result = subprocess.run(
            [python_exec, scraper_path],
            capture_output=True, text=True, timeout=300, cwd=backend_dir
        )
        if result.returncode != 0:
            logger.error(f"Scraper error: {result.stderr[:200]}")
            raise HTTPException(status_code=500, detail="スクレイピング中にエラーが発生しました。")
        
        count = database.get_all_players()
        logger.info(f"Update complete. {len(count)} players in DB.")
        return {"status": "success", "message": f"{len(count)}名の選手データを更新しました。"}
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="スクレイピングがタイムアウトしました。")
    except Exception as e:
        logger.error(f"update_data error: {e}")
        raise HTTPException(status_code=500, detail="更新中にエラーが発生しました。")
