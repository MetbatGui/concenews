"""InMemoryNewsRepository unit tests."""
import pytest

from src.modules.news.domain.models import NewsItem
from src.modules.news.infrastructure.repositories import InMemoryNewsRepository


def _make_item(item_id: int, title: str = "t") -> NewsItem:
    """테스트용 NewsItem 헬퍼."""
    return NewsItem(
        id=item_id,
        title=title,
        link=f"https://example.com/{item_id}",
        source="Reuters",
        published_at="2026-07-03T10:30:00Z",
    )


class TestInMemoryNewsRepository:
    """InMemoryNewsRepository 저장/조회 검증."""

    def test_empty_repository_returns_empty_list(self):
        """빈 저장소는 빈 리스트를 반환한다.

        Given: 초기값 없이 생성된 저장소
        When: find_all() 호출
        Then: 빈 리스트
        """
        repo = InMemoryNewsRepository()
        assert repo.find_all() == []

    def test_save_persists_item(self):
        """저장한 item 은 find_all 에 나타난다.

        Given: 빈 저장소, NewsItem 1개
        When: save(item)
        Then: find_all() 에 해당 item 포함
        """
        repo = InMemoryNewsRepository()
        item = _make_item(1)

        repo.save(item)

        assert repo.find_all() == [item]

    def test_save_multiple_items_persists_all(self):
        """여러 item 저장 시 모두 반환.

        Given: 빈 저장소, NewsItem 2개
        When: 각각 save
        Then: find_all() 에 2개 모두 포함
        """
        repo = InMemoryNewsRepository()
        item1 = _make_item(1, title="A")
        item2 = _make_item(2, title="B")

        repo.save(item1)
        repo.save(item2)

        result = repo.find_all()
        assert len(result) == 2
        assert item1 in result
        assert item2 in result

    def test_save_same_id_updates_existing(self):
        """같은 id 로 save 시 기존 값 갱신 (upsert).

        Given: id=1 로 item1 저장
        When: 같은 id=1 로 item2 저장 (다른 title)
        Then: find_all() 에 item2 만 존재 (item1 대체)
        """
        repo = InMemoryNewsRepository()
        item1 = _make_item(1, title="원본")
        item2 = _make_item(1, title="갱신")

        repo.save(item1)
        repo.save(item2)

        result = repo.find_all()
        assert len(result) == 1
        assert result[0].title == "갱신"

    def test_initial_populates_repository(self):
        """initial 파라미터로 사전 저장 상태 생성.

        Given: NewsItem 2개를 initial 로 전달
        When: 저장소 생성 후 find_all()
        Then: initial 의 2개 아이템 모두 반환
        """
        item1 = _make_item(1)
        item2 = _make_item(2)

        repo = InMemoryNewsRepository(initial=[item1, item2])

        result = repo.find_all()
        assert len(result) == 2
        assert item1 in result
        assert item2 in result
