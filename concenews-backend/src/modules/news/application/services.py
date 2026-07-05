"""News 모듈 application 계층 서비스."""
from src.modules.news.domain.models import NewsItem
from src.modules.news.infrastructure.repositories import InMemoryNewsRepository


class NewsService:
    """뉴스 조회 서비스.

    Repository 에서 뉴스를 읽어 정렬 + limit 적용 후 반환.

    Attributes:
        _repository: 뉴스 저장소 (구체 InMemoryNewsRepository).
            두 번째 impl (PostgreSQL 등) 등장 시 Protocol 추출.
    """

    def __init__(self, repository: InMemoryNewsRepository):
        self._repository = repository

    def fetch_news(self, limit: int) -> list[NewsItem]:
        """정렬된 뉴스를 limit 개 반환.

        Args:
            limit: 반환할 최대 아이템 수 (valid 가정, endpoint 검증).

        Returns:
            published_at 내림차순으로 정렬된 NewsItem 리스트 (최대 limit 개).
        """
        items = self._repository.find_all()
        items.sort(key=lambda item: item.published_at, reverse=True)
        return items[:limit]
