"""NewsCollectorService unit tests.

GWT (Given-When-Then) 형식.
"""
from datetime import datetime, timezone
from uuid import UUID

import pytest

from src.modules.news.domain.models import NewsItem
from src.modules.news.application.services import NewsCollectorService


class FakeCache:
    """Test fake for CachePort."""

    def __init__(self) -> None:
        self.cache: dict[str, float] = {}

    def contains(self, key: str) -> bool:
        return key in self.cache

    def set(self, key: str, ttl_seconds: int) -> None:
        self.cache[key] = 1.0


class FakeRepository:
    """Test fake for NewsRepositoryPort."""

    def __init__(self) -> None:
        self.items: list[NewsItem] = []
        self.save_calls: list[NewsItem] = []

    def save(self, item: NewsItem) -> None:
        self.items.append(item)
        self.save_calls.append(item)

    def find_all(self) -> list[NewsItem]:
        return self.items


class FakeNewsSource:
    """Test fake for NewsSourcePort."""

    def __init__(self, articles: list[NewsItem]) -> None:
        self.articles = articles

    def fetch(self, keywords: list[str]) -> list[NewsItem]:
        return self.articles


@pytest.fixture
def cache():
    return FakeCache()


@pytest.fixture
def repository():
    return FakeRepository()


def test_collector_fetches_from_api():
    """Given: API에서 기사 반환
    When: collector.run(keywords) 호출
    Then: API 호출 후 기사 수집
    """
    article1 = NewsItem(
        id=UUID("019f3676-c27a-7000-0000-000000000001"),
        title="News 1",
        description=None,
        link="https://example.com/1",
        source="Source A",
        published_at=datetime.now(timezone.utc),
        keywords="",
        categories=(),
    )

    source = FakeNewsSource([article1])
    cache = FakeCache()
    repository = FakeRepository()

    collector = NewsCollectorService(
        news_source=source, cache=cache, repository=repository
    )

    collector.run(keywords=["test"])

    assert len(repository.save_calls) == 1
    assert repository.save_calls[0].title == "News 1"


def test_collector_skips_cached_articles(cache, repository):
    """Given: 기사가 이미 캐시됨
    When: collector.run(keywords) 호출
    Then: 캐시 확인 후 skip, DB 저장 안 함
    """
    article1 = NewsItem(
        id=UUID("019f3676-c27a-7000-0000-000000000001"),
        title="Cached News",
        description=None,
        link="https://cached-link.com",
        source="Source A",
        published_at=datetime.now(timezone.utc),
        keywords="",
        categories=(),
    )

    # 사전 캐시 설정
    cache.set("https://cached-link.com", ttl_seconds=900)

    source = FakeNewsSource([article1])
    collector = NewsCollectorService(
        news_source=source, cache=cache, repository=repository
    )

    collector.run(keywords=[])

    # 기사가 캐시되어 있으므로 저장 안 됨
    assert len(repository.save_calls) == 0


def test_collector_caches_after_save(cache, repository):
    """Given: DB 저장 성공
    When: collector.run() 호출
    Then: 캐시에도 저장
    """
    article1 = NewsItem(
        id=UUID("019f3676-c27a-7000-0000-000000000001"),
        title="News",
        description=None,
        link="https://example.com/news",
        source="Source",
        published_at=datetime.now(timezone.utc),
        keywords="",
        categories=(),
    )

    source = FakeNewsSource([article1])
    collector = NewsCollectorService(
        news_source=source, cache=cache, repository=repository
    )

    collector.run(keywords=[])

    # 저장 후 캐시 확인
    assert cache.contains("https://example.com/news")


def test_collector_handles_multiple_articles(cache, repository):
    """Given: API에서 여러 기사 반환
    When: collector.run() 호출
    Then: 각 기사별 dedup 처리
    """
    articles = [
        NewsItem(
            id=UUID("019f3676-c27a-7000-0000-000000000001"),
            title="News 1",
            description=None,
            link="https://example.com/1",
            source="Source",
            published_at=datetime.now(timezone.utc),
            keywords="",
            categories=(),
        ),
        NewsItem(
            id=UUID("019f3676-c27a-7000-0000-000000000002"),
            title="News 2",
            description=None,
            link="https://example.com/2",
            source="Source",
            published_at=datetime.now(timezone.utc),
            keywords="",
            categories=(),
        ),
    ]

    source = FakeNewsSource(articles)
    collector = NewsCollectorService(
        news_source=source, cache=cache, repository=repository
    )

    collector.run(keywords=[])

    assert len(repository.save_calls) == 2
    assert cache.contains("https://example.com/1")
    assert cache.contains("https://example.com/2")


def test_collector_dedup_by_link(cache, repository):
    """Given: 같은 link 기사 2개 (중복)
    When: collector.run() 호출
    Then: 첫 번째만 저장, 두 번째는 캐시됨
    """
    article = NewsItem(
        id=UUID("019f3676-c27a-7000-0000-000000000001"),
        title="News",
        description=None,
        link="https://example.com/duplicate",
        source="Source",
        published_at=datetime.now(timezone.utc),
        keywords="",
        categories=(),
    )

    source = FakeNewsSource([article, article])  # 같은 기사 2번
    collector = NewsCollectorService(
        news_source=source, cache=cache, repository=repository
    )

    collector.run(keywords=[])

    # 첫 번째만 저장, 두 번째는 캐시 되어 skip
    assert len(repository.save_calls) == 1
