from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import settings
from app.db import Base, engine, get_db, SessionLocal
from app.models import Game, BacktestRun
from app.ingestion import ingest_football, ingest_basketball
from app.backtesting import run_backtest
from app.schemas import BacktestRequest

scheduler = AsyncIOScheduler()

async def scheduled_ingest():
    db = SessionLocal()
    try:
        try:
            await ingest_football(db)
        except Exception as exc:
            print(f"Scheduled football ingestion failed: {exc}")
        try:
            await ingest_basketball(db)
        except Exception as exc:
            print(f"Scheduled basketball ingestion failed: {exc}")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.ingestion_enabled:
        scheduler.add_job(scheduled_ingest, "interval", hours=max(1, settings.ingestion_interval_hours),
                          id="sports-ingestion", replace_existing=True, max_instances=1)
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)

app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok", "product": settings.app_name, "version": "0.2.0"}

@app.get("/coverage")
def coverage(db: Session = Depends(get_db)):
    rows = db.execute(select(Game.sport, Game.provider, Game.competition, func.count(Game.id))
                      .group_by(Game.sport, Game.provider, Game.competition)).all()
    return [{"sport": r[0], "provider": r[1], "competition": r[2], "games": r[3]} for r in rows]

@app.get("/games")
def games(sport: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    q = select(Game).order_by(Game.scheduled_at.desc()).limit(min(max(limit, 1), 500))
    if sport:
        q = q.where(Game.sport == sport)
    rows = db.scalars(q).all()
    return [{"id": g.id, "sport": g.sport, "competition": g.competition, "home_team": g.home_team,
             "away_team": g.away_team, "scheduled_at": g.scheduled_at, "status": g.status,
             "home_score": g.home_score, "away_score": g.away_score, "provider": g.provider} for g in rows]

@app.post("/admin/ingest/football")
async def ingest_football_endpoint(db: Session = Depends(get_db)):
    try:
        return await ingest_football(db)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

@app.post("/admin/ingest/basketball")
async def ingest_basketball_endpoint(db: Session = Depends(get_db)):
    try:
        return await ingest_basketball(db)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@app.post("/admin/backfill/football")
async def backfill_football(date_from: str = Query(..., description="YYYY-MM-DD"),
                            date_to: str = Query(..., description="YYYY-MM-DD"),
                            db: Session = Depends(get_db)):
    try:
        return await ingest_football(db, date_from=date_from, date_to=date_to)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

@app.post("/admin/backfill/basketball")
async def backfill_basketball(date_from: str | None = None, date_to: str | None = None,
                              season: int | None = None, db: Session = Depends(get_db)):
    try:
        if not date_from and not date_to and season is None:
            raise HTTPException(status_code=400, detail="Supply a date range or season")
        return await ingest_basketball(db, date_from=date_from, date_to=date_to, season=season)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))

@app.post("/backtests/run")
def backtest(req: BacktestRequest, db: Session = Depends(get_db)):
    try:
        return run_backtest(db, req.sport, req.min_train_games)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.get("/backtests")
def backtests(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.scalars(select(BacktestRun).order_by(BacktestRun.started_at.desc()).limit(min(max(limit,1),100))).all()
    return [{"id": r.id, "sport": r.sport, "model": r.model_name, "games_evaluated": r.games_evaluated,
             "accuracy": r.accuracy, "log_loss": r.log_loss, "brier_score": r.brier_score,
             "started_at": r.started_at} for r in rows]
