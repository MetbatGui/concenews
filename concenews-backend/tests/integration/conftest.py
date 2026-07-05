"""Integration test 공통 fixture.

testing.md: 사용 범위별 위치. 여기는 integration 전체 공유.
Sub-fixture (모듈 별) 는 tests/integration/{module}/conftest.py 에 위치.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from uuid_utils.compat import uuid7

from src.main import app
from src.modules.news.domain.models import NewsItem
from src.modules.news.infrastructure.repositories import InMemoryNewsRepository
from src.modules.news.bootstrap import get_repository


@pytest.fixture
def empty_repository() -> InMemoryNewsRepository:
    """빈 InMemoryNewsRepository."""
    return InMemoryNewsRepository()


@pytest.fixture
def client(empty_repository: InMemoryNewsRepository) -> TestClient:
    """FastAPI TestClient — 기본 empty repository 주입.

    Args:
        empty_repository: 빈 저장소 fixture.

    Yields:
        TestClient. 종료 시 dependency override 정리.
    """
    app.dependency_overrides[get_repository] = lambda: empty_repository
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _make_news(
    title: str = "뉴스",
    published_at: datetime | None = None,
) -> NewsItem:
    """Integration 용 NewsItem 팩토리.

    Args:
        title: 뉴스 제목.
        published_at: 발행 시간. None 이면 현재 UTC.

    Returns:
        NewsItem (id 자동 발급).
    """
    when = published_at or datetime.now(timezone.utc)
    return NewsItem(
        id=uuid7(),
        title=title,
        link=f"https://example.com/{uuid7()}",
        source="Reuters",
        published_at=when,
    )
