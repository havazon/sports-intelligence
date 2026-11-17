from pydantic import BaseModel, Field

class BacktestRequest(BaseModel):
    sport: str = Field(pattern="^(football|basketball)$")
    min_train_games: int = Field(default=30, ge=5, le=10000)
