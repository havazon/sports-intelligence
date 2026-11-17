from datetime import datetime
import httpx
from app.config import settings
from app.providers.base import SportsProvider, ProviderError

class FootballDataProvider(SportsProvider):
    name = "football-data.org"
    base_url = "https://api.football-data.org/v4"

    async def fetch_games(self, date_from: str | None = None, date_to: str | None = None) -> list[dict]:
        if not settings.football_data_api_key:
            raise ProviderError("FOOTBALL_DATA_API_KEY is not configured")
        headers = {"X-Auth-Token": settings.football_data_api_key}
        async with httpx.AsyncClient(timeout=30) as client:
            params = {}
            if date_from: params["dateFrom"] = date_from
            if date_to: params["dateTo"] = date_to
            response = await client.get(f"{self.base_url}/matches", headers=headers, params=params)
            if response.status_code == 429:
                raise ProviderError("football-data.org rate limit reached")
            response.raise_for_status()
            payload = response.json()
        result = []
        for m in payload.get("matches", []):
            home, away = m.get("homeTeam") or {}, m.get("awayTeam") or {}
            score = m.get("score") or {}
            ft = score.get("fullTime") or {}
            utc = m.get("utcDate")
            result.append({
                "sport": "football",
                "competition": (m.get("competition") or {}).get("name"),
                "season": str((m.get("season") or {}).get("startDate", ""))[:4] or None,
                "provider": self.name,
                "provider_game_id": str(m["id"]),
                "home_team": home.get("name") or "Unknown home team",
                "away_team": away.get("name") or "Unknown away team",
                "home_team_provider_id": str(home.get("id")) if home.get("id") else None,
                "away_team_provider_id": str(away.get("id")) if away.get("id") else None,
                "scheduled_at": datetime.fromisoformat(utc.replace("Z", "+00:00")) if utc else None,
                "status": (m.get("status") or "SCHEDULED").lower(),
                "home_score": ft.get("home"),
                "away_score": ft.get("away"),
                "venue": None,
                "raw_payload": m,
            })
        return result
