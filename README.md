# Havazon Sports Intelligence

Research-first football and basketball analytics platform.

This repository is being initialised from the validated Phase 2 backend starter. The first source package is provided in `artifacts/havazon-sports-intelligence-phase2.zip` while the project is expanded into its browsable source tree.

## Included in Phase 2

- FastAPI backend and SQLAlchemy data model
- PostgreSQL-ready Docker Compose setup
- Initial football-data.org and BALLDONTLIE ingestion adapters
- Scheduled and manual ingestion endpoints
- Chronological baseline backtesting for football (Poisson 1X2) and basketball (Elo-style winner probabilities)
- Accuracy, log loss and Brier score metrics
- Pytest suite and GitHub Actions workflow

## Local setup

Extract the source archive, copy `.env.example` to `.env`, configure provider credentials, then run `docker compose up --build`. The API documentation is available at `http://localhost:8000/docs`.

## Important

The provider connectors are starter integrations and have not yet been validated against live credentials. Competition coverage depends on provider plans and licensing. The baseline models are research tools, not guaranteed predictions or evidence of profitability. Never commit API keys or `.env` files.
