from __future__ import annotations

from functools import lru_cache
from os import getenv

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "AquaTrack API"
    debug: bool = False

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Must be >= 32 bytes: PyJWT warns on shorter HMAC keys, so the development
    # default is padded to satisfy RFC 7518. Always override in production.
    secret_key: str = getenv("SECRET_KEY", "dev-secret-change-in-prod-not-for-production")
    access_token_ttl_minutes: int = 60 * 24 * 7

    database_url_sync: str = getenv(
        "DATABASE_URL", "sqlite+aiosqlite:///./aquatrack.db"
    )
    database_url_async: str = getenv(
        "DATABASE_URL_ASYNC", "sqlite+aiosqlite:///./aquatrack.db"
    )
    # Production path: set DATABASE_URL to a postgresql://... URL and install asyncpg.
    # The MVP defaults to SQLite so it runs without a local Postgres instance.
    # PostGIS geography columns are not used for any spatial SQL in the MVP; the
    # geography column in models.py is kept as documentation of the intended
    # production schema and is gated behind a PostGIS DB.
    # Postgres schema that AquaTrack's tables live in. Empty means "whatever the
    # connection's default search_path resolves to" (fine for SQLite). Set this to
    # `aquatrack` to keep the tables isolated from other applications that share the
    # same Postgres instance.
    database_schema: str = getenv("DATABASE_SCHEMA", "")
    database_echo: bool = False

    openmeteo_base_url: str = "https://marine-api.open-meteo.com/v1/"
    # The Marine API is ocean-only and serves no wind/weather variables, so wind and
    # weather_code come from the standard weather forecast API instead.
    openmeteo_weather_base_url: str = "https://api.open-meteo.com/v1/"
    openmeteo_cache_ttl_seconds: int = 600

    predictions_cache_ttl_seconds: int = 600
    grid_resolution_km: float = 10.0

    @property
    def openmeteo_marine_url(self) -> str:
        return self.openmeteo_base_url + "marine"

    @property
    def openmeteo_weather_url(self) -> str:
        return self.openmeteo_weather_base_url + "forecast"


@lru_cache
def get_settings() -> Settings:
    return Settings()
