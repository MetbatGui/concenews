"""DB 설정 (Pydantic Settings).

환경 변수 (.env) 로 DATABASE_URL 관리.
상세: docs/decisions/2026-07-06-db-library.md
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DbSettings(BaseSettings):
    """DB 관련 설정.

    Attributes:
        database_url: SQLAlchemy DSN (예: postgresql+psycopg://user:pass@host:port/db).
    """

    database_url: str = Field(
        default="postgresql+psycopg://concenews:concenews@localhost:5432/concenews",
        alias="DATABASE_URL",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = DbSettings()
