"""DB 설정 (env-driven).

App startup / test setup 에서 load_config() 명시 호출로 .env 로드.
Test 는 load_config(".env.test") 로 격리.
상세: docs/decisions/2026-07-06-db-library.md
"""
import os

from dotenv import load_dotenv

DEFAULT_DATABASE_URL = "postgresql+psycopg://concenews:concenews@localhost:5432/concenews"


def load_config(env_file: str = ".env") -> None:
    """Env file 명시 로드. App startup 또는 test setup 에서 호출.

    Args:
        env_file: .env 파일 경로 (default: ".env"). Test 는 ".env.test" 로 호출.
    """
    load_dotenv(env_file)


def get_database_url() -> str:
    """Production DATABASE_URL.

    Returns:
        환경 변수 DATABASE_URL 값. 없으면 dev 기본값 (localhost:5432).
    """
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
