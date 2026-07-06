"""News 모듈 application 계층 서비스."""
import logging

from src.modules.news.application.exceptions import CollectionError
from src.modules.news.application.ports import CachePort, NewsRepositoryPort, NewsSourcePort
from src.modules.news.domain.models import NewsItem

logger = logging.getLogger(__name__)


class NewsService:
    """뉴스 조회 서비스.

    Repository 에서 뉴스를 읽어 정렬 + limit 적용 후 반환.

    Attributes:
        _repository: 뉴스 저장소 (Port).
    """

    def __init__(self, repository: NewsRepositoryPort):
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


class NewsCollectorService:
    """뉴스 수집 서비스 (백그라운드).

    외부 뉴스 소스에서 기사를 가져와 DB에 저장.
    Cache로 중복 방지 (dedup by link).

    Flow: API → Cache check → DB save → Cache set

    Attributes:
        news_source: 뉴스 소스 (외부 API).
        cache: 캐시 (link → TTL).
        repository: 뉴스 저장소 (DB).
    """

    def __init__(
        self,
        news_source: NewsSourcePort,
        cache: CachePort,
        repository: NewsRepositoryPort,
    ) -> None:
        """Initialize collector.

        Args:
            news_source: NewsSourcePort 구현.
            cache: CachePort 구현.
            repository: NewsRepositoryPort 구현.
        """
        self.news_source = news_source
        self.cache = cache
        self.repository = repository

    def run(self, keywords: list[str]) -> None:
        """뉴스 수집 및 저장.

        Cache에서 확인 후, 미포함 시 DB 저장 후 캐시 등록.
        부분 성공 허용 (실패 시 로그, 다음 기사 계속).

        Args:
            keywords: 검색 키워드.

        Raises:
            CollectionError: API 호출 실패 시 (전체 실패).
        """
        try:
            articles = self.news_source.fetch(keywords)
        except Exception as e:
            msg = f"API 호출 실패: {e}"
            logger.error(msg)
            raise CollectionError(msg) from e

        for article in articles:
            try:
                # 캐시 확인 (dedup 1차)
                if self.cache.contains(article.link):
                    continue

                # DB 저장 (dedup 2차, unique link constraint)
                self.repository.save(article)

                # 캐시 저장 (15분 TTL)
                self.cache.set(article.link, ttl_seconds=900)
            except Exception as e:
                # 부분 성공: 로그만 하고 계속
                logger.warning(f"기사 저장 실패 ({article.link}): {e}")
