from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base

def utcnow():
    return datetime.now(timezone.utc)

class Game(Base):
    __tablename__ = "games"
    __table_args__ = (
        UniqueConstraint("provider", "provider_game_id", name="uq_provider_game"),
        Index("ix_games_sport_date", "sport", "scheduled_at"),
        Index("ix_games_sport_status", "sport", "status"),
    )
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sport: Mapped[str] = mapped_column(String(24), index=True)
    competition: Mapped[str | None] = mapped_column(String(120), nullable=True)
    season: Mapped[str | None] = mapped_column(String(40), nullable=True)
    provider: Mapped[str] = mapped_column(String(60))
    provider_game_id: Mapped[str] = mapped_column(String(120))
    home_team: Mapped[str] = mapped_column(String(160))
    away_team: Mapped[str] = mapped_column(String(160))
    home_team_provider_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    away_team_provider_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="scheduled")
    home_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    away_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(180), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sport: Mapped[str] = mapped_column(String(24), index=True)
    model_name: Mapped[str] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    games_evaluated: Mapped[int] = mapped_column(Integer, default=0)
    accuracy: Mapped[float | None] = mapped_column(Float, nullable=True)
    log_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    brier_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
