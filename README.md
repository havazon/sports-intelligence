# Havazon Sports Intelligence

Research-first football + basketball analytics backend starter.

## What is included

- FastAPI backend
- PostgreSQL-ready SQLAlchemy schema (SQLite works for local development)
- Provider adapter interface
- `football-data.org` match ingestion connector
- `BALLDONTLIE` basketball games ingestion connector (NBA endpoint starter)
- Manual date-range / season backfill endpoints
- Scheduled ingestion with APScheduler
- Walk-forward historical backtesting:
  - Football: rolling team goal-rate Poisson 1X2 probabilities
  - Basketball: rolling Elo-style win probabilities
  - Accuracy, log loss and Brier score
- Provider/source attribution and raw payload storage
- GitHub Actions test workflow
- Dockerfile and docker-compose for local API + PostgreSQL

## Quick start

1. Copy `.env.example` to `.env` and add API keys.
2. Run:

```bash
docker compose up --build
```

3. Open `http://localhost:8000/docs`.

For local Python development without Docker:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Provider credentials

- `FOOTBALL_DATA_API_KEY`: football-data.org token.
- `BALLDONTLIE_API_KEY`: BALLDONTLIE API key.
- `DATABASE_URL`: PostgreSQL connection string. Defaults to local SQLite.

Never commit `.env` or provider keys. Use GitHub Actions Secrets and deployment-platform secrets.

## Ingestion

Trigger manually:

```bash
curl -X POST http://localhost:8000/admin/ingest/football
curl -X POST http://localhost:8000/admin/ingest/basketball
```

The scheduler also runs ingestion every six hours. This cadence is intentionally conservative; tune it to provider quotas and plan limits.

## Backfilling historical data

Football:

```bash
curl -X POST "http://localhost:8000/admin/backfill/football?date_from=2024-01-01&date_to=2024-12-31"
```

Basketball:

```bash
curl -X POST "http://localhost:8000/admin/backfill/basketball?season=2024"
```

Provider pagination, plan limits and historical coverage need further work before large backfills.

## Backtesting

```bash
curl -X POST http://localhost:8000/backtests/run \
  -H 'Content-Type: application/json' \
  -d '{"sport":"football","min_train_games":30}'
```

For basketball use `"sport":"basketball"`.

Backtests use completed games and chronological expanding windows. Metrics are computed from predictions made before each test game's result is incorporated. A small dataset may produce no eligible predictions; the API reports that rather than fabricating metrics.

## Current limitations

These are transparent baseline models, not production-grade forecasts:
- Football uses rolling goals-for/goals-against rates with a simple Poisson distribution.
- Basketball uses a simple Elo-style rating derived from prior results.
- No injuries, lineups, pace, player availability, rest, odds, market prices, or closing-line data are included yet.
- The starter connectors currently cover only the provider endpoints implemented here, not all global competitions.
- Provider calls have not been validated against live credentials in this environment.
- No ROI claim is made. ROI simulation requires timestamped historical odds and explicit settlement rules.
- Model quality must be measured by competition and market with sufficient sample sizes.
- Review each provider's data licence before commercial use or redistribution.

## Roadmap

1. Add provider-specific competition discovery and a coverage registry.
2. Add richer football statistics, basketball box scores, player availability and odds snapshots.
3. Add time-aware feature snapshots and model versioning.
4. Add calibrated market-specific models and walk-forward validation.
5. Add user accounts, roles, subscriptions and a Next.js dashboard.
