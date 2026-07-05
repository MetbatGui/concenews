"""DB 설정 (.env + os.environ).

.env 파일에서 DATABASE_URL 을 로드하여 os.environ 에 반영.
Test 는 fixture 로 URL 을 직접 주입.
상세: docs/decisions/2026-07-06-db-library.md
"""
import os

from dotenv import load_dotenv

load_dotenv()

DEFAULT_DATABASE_URL = "postgresql+psycopg://concenews:concenews@localhost:5432/concenews"


def get_database_url() -> str:
    """Production 용 DATABASE_URL.

    Returns:
        환경 변수 DATABASE_URL 값. 없으면 dev 기본값 (localhost:5432).
    """
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)
