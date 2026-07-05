"""NewsService unit tests."""
from uuid import UUID

from uuid_utils.compat import uuid7

from src.modules.news.application.services import NewsService
from src.modules.news.domain.models import NewsItem
from src.modules.news.infrastructure.repositories import InMemoryNewsRepository


def _make_item(
    item_id: UUID | None = None,
    published_at: str = "2026-07-03T10:30:00Z",
) -> NewsItem:
    """테스트용 NewsItem 헬퍼.

    Args:
        item_id: 부여할 UUID. None 이면 uuid7 자동 생성.
        published_at: 발행 시간 ISO8601 문자열.

    Returns:
        NewsItem 인스턴스.
    """
    resolved_id = item_id if item_id is not None else uuid7()
    return NewsItem(
        id=resolved_id,
        title=f"뉴스 {resolved_id}",
        link=f"https://example.com/{resolved_id}",
        source="Reuters",
        published_at=published_at,
    )


class TestNewsServiceFetchNews:
    """NewsService.fetch_news 정렬/limit 검증."""

    def test_fetch_news_returns_empty_when_repository_empty(self):
        """빈 저장소는 빈 리스트를 반환한다.

        Given: 빈 Repository
        When: fetch_news(limit=50)
        Then: []
        """
        service = NewsService(repository=InMemoryNewsRepository())

        assert service.fetch_news(limit=50) == []

    def test_fetch_news_returns_all_when_count_below_limit(self):
        """count <= limit 일 때 모든 아이템 반환.

        Given: 3개 저장, limit=50
        When: fetch_news(limit=50)
        Then: 3개 모두 반환
        """
        items = [_make_item() for _ in range(3)]
        service = NewsService(repository=InMemoryNewsRepository(initial=items))

        result = service.fetch_news(limit=50)

        assert len(result) == 3

    def test_fetch_news_sorts_by_published_at_desc(self):
        """published_at 최근순 (내림차순) 으로 정렬.

        Given: 3개 저장 (오래된 것 부터 순서로)
        When: fetch_news(limit=50)
        Then: published_at 내림차순 (최신이 먼저)
        """
        old = _make_item(published_at="2020-01-01T00:00:00Z")
        mid = _make_item(published_at="2023-01-01T00:00:00Z")
        new = _make_item(published_at="2026-01-01T00:00:00Z")
        service = NewsService(
            repository=InMemoryNewsRepository(initial=[old, mid, new])
        )

        result = service.fetch_news(limit=50)

        assert [item.id for item in result] == [new.id, mid.id, old.id]

    def test_fetch_news_respects_limit(self):
        """count > limit 일 때 limit 개만 반환.

        Given: 5개 저장, limit=3
        When: fetch_news(limit=3)
        Then: 정확히 3개 반환 (published_at 최신 3개)
        """
        items = [
            _make_item(published_at=f"2026-07-{day:02d}T00:00:00Z")
            for day in range(1, 6)
        ]
        service = NewsService(repository=InMemoryNewsRepository(initial=items))

        result = service.fetch_news(limit=3)

        expected_ids = [items[4].id, items[3].id, items[2].id]
        assert len(result) == 3
        assert [item.id for item in result] == expected_ids

    def test_fetch_news_preserves_item_fields(self):
        """반환된 item 은 원본 필드를 유지한다.

        Given: 특정 필드 값을 가진 1개 저장
        When: fetch_news(limit=50)
        Then: 반환 item 이 원본과 동일 (모든 필드)
        """
        original = _make_item()
        service = NewsService(
            repository=InMemoryNewsRepository(initial=[original])
        )

        result = service.fetch_news(limit=50)

        assert result == [original]
