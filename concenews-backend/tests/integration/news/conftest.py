"""News integration fixture.

testing.md: 모듈 전용 fixture 는 tests/integration/{module}/conftest.py.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.modules.news.infrastructure.repositories import InMemoryNewsRepository
from src.modules.news.bootstrap import get_repository

from tests.integration.conftest import _make_news


@pytest.fixture
def filled_repository() -> InMemoryNewsRepository:
    """3개 news 를 pre-populate 한 저장소.

    published_at 이 서로 다름 (정렬 검증용).

    Returns:
        InMemoryNewsRepository (3 items).
    """
    return InMemoryNewsRepository(
        initial=[
            _make_news(
                title="오래된 뉴스",
                published_at=datetime.fromisoformat("2020-01-01T00:00:00+00:00"),
            ),
            _make_news(
                title="중간 뉴스",
                published_at=datetime.fromisoformat("2023-01-01T00:00:00+00:00"),
            ),
            _make_news(
                title="최신 뉴스",
                published_at=datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
            ),
        ]
    )


@pytest.fixture
def filled_client(filled_repository: InMemoryNewsRepository) -> TestClient:
    """filled_repository 를 DI 로 주입한 TestClient.

    Args:
        filled_repository: 3개 news 저장된 저장소.

    Yields:
        TestClient.
    """
    app.dependency_overrides[get_repository] = lambda: filled_repository
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
