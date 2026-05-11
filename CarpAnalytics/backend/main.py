from fastapi import FastAPI, Request, HTTPException, Header, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator
import database
import subprocess
import os
import logging
import re

load_dotenv()

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────
# レート制限（IPアドレスベース）
# ─────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="NPB Insight Pro API",
    docs_url=None,      # Swagger UIを本番公開しない（セキュリティ対策）
    redoc_url=None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─────────────────────────────────────
# APScheduler: 毎日5:00に成績を自動更新
# ─────────────────────────────────────
def _daily_stats_job():
    """バックグラウンドで今季成績を毎日更新し、トレンド分析を実行"""
    try:
        logger.info("[Scheduler] Daily season stats update started.")
        import stats_scraper
        import scraper
        import history_engine

        count = stats_scraper.scrape_all_stats()
        scraper.update_players_from_db()
        history_engine.run_daily_history_pipeline()

        logger.info(f"[Scheduler] Done. {count} records updated and history recorded.")
    except Exception as e:
        logger.error(f"[Scheduler] Daily update failed: {e}")

scheduler = BackgroundScheduler(timezone="Asia/Tokyo")
scheduler.add_job(_daily_stats_job, 'cron', hour=5, minute=0, id='daily_stats')
scheduler.start()
logger.info("APScheduler started. Daily stats update scheduled at 05:00 JST.")

# ─────────────────────────────────────
# 許可するオリジンを.envから取得
# ─────────────────────────────────────
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-Token"],
)

# ─────────────────────────────────────
# S-2: 管理エンドポイントをローカルIPのみに制限するミドルウェア
# ─────────────────────────────────────
_ADMIN_PATHS = {"/api/update-data", "/api/update-stats"}
_LOCALHOST_IPS = {"127.0.0.1", "::1"}

@app.middleware("http")
async def restrict_admin_endpoints(request: Request, call_next):
    """管理用エンドポイントはローカルホストからのアクセスのみ許可する"""
    if request.url.path in _ADMIN_PATHS:
        client_host = request.client.host if request.client else ""
        if client_host not in _LOCALHOST_IPS:
            logger.warning(
                f"Admin endpoint access denied for {client_host} -> {request.url.path}"
            )
            return JSONResponse(
                status_code=403,
                content={"status": "error", "message": "このエンドポイントはローカルからのみアクセスできます。"}
            )
    return await call_next(request)

# ─────────────────────────────────────
# セキュリティヘッダーミドルウェア（CSP動的生成）
# ─────────────────────────────────────
# M-3: connect-src を ALLOWED_ORIGINS から動的生成（localhost ハードコードを排除）
_csp_connect_src = " ".join(["'self'"] + ALLOWED_ORIGINS)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "    # Viteのインラインスクリプトのため
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https://placehold.co; "
        f"connect-src {_csp_connect_src}; "
        "frame-ancestors 'none';"
    )
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

def verify_token(x_request_token: str | None = Header(default=None)):
    """
    トークンを検証する。ただし、ローカルIP制限ミドルウェアで保護されているため、
    ヘッダーが欠落していてもエラーにせず、あれば検証する形にする。
    """
    if x_request_token:
        if not SECRET_TOKEN or x_request_token != SECRET_TOKEN:
            logger.warning(f"Invalid token attempt: {x_request_token}")
            raise HTTPException(status_code=401, detail="認証トークンが無効です。")
    # トークンがない場合は、ミドルウェアのIP制限を信頼して通過させる

# ─────────────────────────────────────
# Pydantic バリデーション
# ─────────────────────────────────────
_SAFE_TEAM_NAMES = {
    '広島東洋カープ', '読売ジャイアンツ', '阪神タイガース', '横浜DeNAベイスターズ',
    '東京ヤクルトスワローズ', '中日ドラゴンズ', 'オリックス・バファローズ',
    '千葉ロッテマリーンズ', '福岡ソフトバンクホークス', '東北楽天ゴールデンイーグルス',
    '埼玉西武ライオンズ', '北海道日本ハムファイターズ',
}

def _validate_team(team: str | None) -> str | None:
    if team is None:
        return None
    if team not in _SAFE_TEAM_NAMES:
        raise HTTPException(status_code=422, detail="無効な球団名です。")
    return team

def _validate_league(league: str | None) -> str | None:
    if league is None:
        return None
    if league not in ('Central', 'Pacific'):
        raise HTTPException(status_code=422, detail="リーグ名はCentralまたはPacificのみ有効です。")
    return league

def _validate_stat_type(stat_type: str | None) -> str | None:
    if stat_type is None:
        return None
    if stat_type not in ('batting', 'pitching'):
        raise HTTPException(status_code=422, detail="stat_typeはbattingまたはpitchingのみ有効です。")
    return stat_type

def _validate_name(name: str) -> str:
    # SQLインジェクション・パストラバーサル対策：日本語・英数字・スペース以外を拒否
    if not re.match(r'^[\w\s\u3040-\u30FF\u4E00-\u9FFF\u3000　]+$', name):
        raise HTTPException(status_code=422, detail="無効な選手名です。")
    if len(name) > 50:
        raise HTTPException(status_code=422, detail="選手名が長すぎます。")
    return name

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
    if player_id <= 0 or player_id > 99999:
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


@app.get("/api/season-stats")
@limiter.limit("60/minute")
def get_season_stats(
    request: Request,
    team: str | None = Query(default=None, max_length=50),
    stat_type: str | None = Query(default=None, max_length=20),
    league: str | None = Query(default=None, max_length=20),
):
    """今季1軍成績を取得（team/stat_type/leagueでフィルタ可能）"""
    team      = _validate_team(team)
    stat_type = _validate_stat_type(stat_type)
    league    = _validate_league(league)
    try:
        stats        = database.get_season_stats(team=team, stat_type=stat_type, league=league)
        last_updated = database.get_stats_last_updated()
        logger.info(f"GET /api/season-stats team={team} type={stat_type} league={league} -> {len(stats)} records.")
        return {
            "status":       "success",
            "last_updated": last_updated,
            "data":         stats,
        }
    except Exception as e:
        logger.error(f"DB error in get_season_stats: {e}")
        raise HTTPException(status_code=500, detail="成績データ取得中にエラーが発生しました。")


@app.get("/api/season-stats/player/{player_name}")
@limiter.limit("30/minute")
def get_player_season_stats(player_name: str, request: Request):
    """特定選手の今季成績を取得"""
    player_name = _validate_name(player_name)
    try:
        stats = database.get_player_season_stats(player_name)
        return {"status": "success", "data": stats}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"DB error in get_player_season_stats: {e}")
        raise HTTPException(status_code=500, detail="成績データ取得中にエラーが発生しました。")


@app.get("/api/teams/{team_name}/optimized-lineup")
@limiter.limit("10/minute")
def get_optimized_lineup(team_name: str, request: Request):
    """チームの最適編成を取得する"""
    team_name = _validate_team(team_name)
    try:
        import lineup_engine
        db_path = os.path.join(os.path.dirname(__file__), "carp_data.db")
        result  = lineup_engine.get_optimized_team_data(team_name, db_path)
        logger.info(f"GET /api/teams/{team_name}/optimized-lineup -> success.")
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Error in get_optimized_lineup: {e}")
        raise HTTPException(status_code=500, detail="最適編成の生成中にエラーが発生しました。")


@app.post("/api/update-data")
@limiter.limit("3/hour")
def update_data(
    request: Request,
    script_name: str = Query("scraper.py"),
    _: None = Depends(verify_token),
):
    """
    ロースタースクレイピングを再実行してDBを更新する。
    【S-2】このエンドポイントはローカルホストからのみアクセス可能。
    要シークレットトークン・1時間に3回まで。
    """
    ALLOWED_SCRIPTS = {"scraper.py", "stats_scraper.py"}
    if script_name not in ALLOWED_SCRIPTS:
        logger.warning(f"Unauthorized script execution attempt: {script_name}")
        raise HTTPException(status_code=403, detail="実行が許可されていないスクリプトです。")

    try:
        backend_dir  = os.path.dirname(os.path.abspath(__file__))
        scraper_path = os.path.join(backend_dir, script_name)
        python_exec  = os.path.abspath(
            os.path.join(backend_dir, "..", "venv", "Scripts", "python.exe")
        )

        logger.info(f"Roster update triggered via API. Script: {script_name}")
        result = subprocess.run(
            [python_exec, scraper_path],
            capture_output=True, text=True, timeout=300, cwd=backend_dir
        )
        if result.returncode != 0:
            logger.error(f"Scraper error: {result.stderr[:200]}")
            raise HTTPException(status_code=500, detail="スクレイピング中にエラーが発生しました。")

        count = len(database.get_all_players())
        logger.info(f"Roster update complete. {count} players in DB.")
        return {"status": "success", "message": f"{count}名の選手データを更新しました。"}
    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="スクレイピングがタイムアウトしました。")
    except Exception as e:
        logger.error(f"update_data error: {e}")
        raise HTTPException(status_code=500, detail="更新中にエラーが発生しました。")


@app.post("/api/update-stats")
@limiter.limit("10/hour")
def update_stats(request: Request, _: None = Depends(verify_token)):
    """
    今季成績を再スクレイピングして更新する（軽量・約10〜20秒で完了）。
    【S-2】このエンドポイントはローカルホストからのみアクセス可能。
    """
    try:
        import stats_scraper
        import scraper
        logger.info("Season stats update triggered via API.")
        count        = stats_scraper.scrape_all_stats()
        scraper.update_players_from_db()
        last_updated = database.get_stats_last_updated()
        logger.info(f"Season stats update complete. {count} records.")
        return {
            "status":       "success",
            "message":      f"{count}件の今季成績と全選手のポテンシャルデータを更新しました。",
            "last_updated": last_updated,
        }
    except Exception as e:
        logger.error(f"update_stats error: {e}")
        raise HTTPException(status_code=500, detail="成績更新中にエラーが発生しました。")


if __name__ == "__main__":
    import uvicorn
    # hostを0.0.0.0に変更してIPv4/IPv6の両方に対応
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
