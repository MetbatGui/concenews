"""News 모듈 저장소 구현."""
from src.modules.news.domain.models import NewsItem


class InMemoryNewsRepository:
    """뉴스 in-memory 저장소.

    Dict 기반 (id → NewsItem). 재시작 시 데이터 소실.
    PostgreSQL 도입 시 동일 인터페이스로 교체 예정.

    Attributes:
        _items: id → NewsItem 매핑.
    """

    def __init__(self, initial: list[NewsItem] | None = None):
        self._items: dict[int, NewsItem] = {}
        for item in initial or []:
            self.save(item)

    def save(self, item: NewsItem) -> None:
        """뉴스 저장 (upsert). 같은 id 존재 시 update.

        Args:
            item: 저장할 NewsItem (id 필수).
        """
        self._items[item.id] = item

    def find_all(self) -> list[NewsItem]:
        """저장된 모든 뉴스 반환.

        순서 미보장. 정렬은 Service 책임.

        Returns:
            NewsItem 리스트.
        """
        return list(self._items.values())
