from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Havazon Sports Intelligence"
    environment: str = "development"
    database_url: str = "sqlite:///./havazon_sports.db"
    football_data_api_key: str | None = None
    balldontlie_api_key: str | None = None
    ingestion_enabled: bool = True
    ingestion_interval_hours: int = 6
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

settings = Settings()
