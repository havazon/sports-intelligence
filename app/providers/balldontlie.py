from datetime import datetime, timezone
import httpx
from app.config import settings
from app.providers.base import SportsProvider, ProviderError

class BallDontLieProvider(SportsProvider):
    name = "balldontlie"
    base_url = "https://api.balldontlie.io/v1"

    async def fetch_games(self, date_from: str | None = None, date_to: str | None = None, season: int | None = None) -> list[dict]:
        if not settings.balldontlie_api_key:
            raise ProviderError("BALLDONTLIE_API_KEY is not configured")
        headers = {"Authorization": settings.balldontlie_api_key}
        # Current/upcoming/recent NBA schedule. Historical season backfills should be
        # implemented as bounded season/date-range jobs to respect account quotas.
        async with httpx.AsyncClient(timeout=30) as client:
            params = {"per_page": 100}
            if date_from: params["start_date"] = date_from
            if date_to: params["end_date"] = date_to
            if season is not None: params["seasons[]"] = season
            response = await client.get(f"{self.base_url}/games", headers=headers, params=params)
            if response.status_code == 429:
                raise ProviderError("BALLDONTLIE rate limit reached")
            response.raise_for_status()
            payload = response.json()
        result = []
        for g in payload.get("data", []):
            home, away = g.get("home_team") or {}, g.get("visitor_team") or {}
            game_date = g.get("date")
            scheduled = None
            if game_date:
                try:
                    scheduled = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
                    if scheduled.tzinfo is None:
                        scheduled = scheduled.replace(tzinfo=timezone.utc)
                except ValueError:
                    scheduled = None
            is_final = str(g.get("status", "")).lower() == "final"
            result.append({
                "sport": "basketball",
                "competition": "NBA",
                "season": str(g.get("season")) if g.get("season") is not None else None,
                "provider": self.name,
                "provider_game_id": str(g["id"]),
                "home_team": home.get("full_name") or home.get("name") or "Unknown home team",
                "away_team": away.get("full_name") or away.get("name") or "Unknown away team",
                "home_team_provider_id": str(home.get("id")) if home.get("id") else None,
                "away_team_provider_id": str(away.get("id")) if away.get("id") else None,
                "scheduled_at": scheduled,
                "status": "finished" if is_final else "scheduled",
                "home_score": g.get("home_team_score"),
                "away_score": g.get("visitor_team_score"),
                "venue": None,
                "raw_payload": g,
            })
        return result
