from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Game
from app.providers.football_data import FootballDataProvider
from app.providers.balldontlie import BallDontLieProvider

async def ingest_provider(db: Session, provider) -> dict:
    rows = await provider.fetch_games()
    return _save_rows(db, provider.name, rows)

async def ingest_football(db: Session, date_from: str | None = None, date_to: str | None = None):
    provider = FootballDataProvider()
    rows = await provider.fetch_games(date_from=date_from, date_to=date_to)
    return _save_rows(db, provider.name, rows)

async def ingest_basketball(db: Session, date_from: str | None = None, date_to: str | None = None, season: int | None = None):
    provider = BallDontLieProvider()
    rows = await provider.fetch_games(date_from=date_from, date_to=date_to, season=season)
    return _save_rows(db, provider.name, rows)

def _save_rows(db: Session, provider_name: str, rows: list[dict]) -> dict:
    inserted = updated = 0
    for row in rows:
        existing = db.scalar(select(Game).where(
            Game.provider == row["provider"], Game.provider_game_id == row["provider_game_id"]
        ))
        if existing:
            for key, value in row.items():
                setattr(existing, key, value)
            updated += 1
        else:
            db.add(Game(**row))
            inserted += 1
    db.commit()
    return {"provider": provider_name, "fetched": len(rows), "inserted": inserted, "updated": updated}
