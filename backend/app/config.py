from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_anon_key: str = ""
    session_secret: str = "change-me-in-production"
    session_expire_hours: int = 24
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    sports_api_key: str = ""
    sports_api_provider: str = "thestatsapi"
    sportmonks_league_id: int = 732
    sportmonks_season_id: int = 26618
    thestatsapi_competition_id: str = ""
    thestatsapi_season_id: str = ""
    sports_sync_interval: int = 30
    attendance_bonus_points: int = 4
    admin_secret: str = "admin-secret-change-me"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sportmonks_enabled(self) -> bool:
        return bool(self.sports_api_key) and self.sports_api_provider == "sportmonks"

    @property
    def thestatsapi_enabled(self) -> bool:
        return bool(self.sports_api_key) and self.sports_api_provider == "thestatsapi"

    @property
    def sports_sync_enabled(self) -> bool:
        return self.sportmonks_enabled or self.thestatsapi_enabled

    class Config:
        env_file = ".env"


settings = Settings()
