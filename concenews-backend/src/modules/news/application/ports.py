"""News 모듈 application 계층 ports (인터페이스).

Hexagonal architecture 원칙:
- Port (인터페이스) 는 안쪽 (application) 이 정의.
- Adapter (구현) 는 바깥쪽 (infrastructure) 이 구현.
- Dependency Inversion: infrastructure → application.
"""
from collections.abc import Awaitable, Callable
from typing import Protocol
from uuid import UUID

from src.modules.news.domain.models import NewsItem


class IdGenerator(Protocol):
    """Identity 발급 port.

    구현체는 매 호출마다 unique identity 반환.
    """

    def generate(self) -> UUID:
        """다음 identity 반환."""
        ...


class NewsRepositoryPort(Protocol):
    """뉴스 저장소 port.

    구현체 (Adapter):
    - Production: PgNewsRepository (infrastructure/repositories/postgres.py)
    - Test Fake: InMemoryNewsRepository (infrastructure/repositories/in_memory.py)

    상세: docs/decisions/2026-07-06-repository-strategy.md
    """

    def save(self, item: NewsItem) -> None:
        """뉴스 저장 (upsert). 같은 id 존재 시 update.

        Args:
            item: 저장할 NewsItem.
        """
        ...

    def find_all(self) -> list[NewsItem]:
        """저장된 모든 뉴스 반환.

        순서 미보장. 정렬은 Service 책임.

        Returns:
            NewsItem 리스트.
        """
        ...


class CachePort(Protocol):
    """재요청 방지 캐시 port.

    구현체 (Adapter):
    - Production: InMemoryCacheAdapter (dict + TTL)
    - Future: RedisCacheAdapter (Redis 대체 가능)

    상세: plan-news-collection.md § Cache impl 참고 (stdlib dict+TTL 선택)
    """

    def set(self, key: str, ttl_seconds: int) -> None:
        """캐시 항목 저장.

        Args:
            key: 캐시 키 (뉴스 링크).
            ttl_seconds: TTL (초).
        """
        ...

    def contains(self, key: str) -> bool:
        """캐시 항목 존재 여부 확인.

        만료된 항목은 자동 제거 후 False 반환.

        Args:
            key: 캐시 키.

        Returns:
            key 가 캐시에 유효하면 True.
        """
        ...


class SchedulerPort(Protocol):
    """정기 job 실행 port.

    구현체 (Adapter):
    - Production: AsyncioSchedulerAdapter (PR #7, FastAPI lifespan 통합)
    - Test: FakeScheduler (trigger_all() 로 수동 실행)

    상세: docs/decisions/2026-07-06-scheduler-choice.md
    """

    def schedule(
        self, func: Callable[[], Awaitable[None]], interval_seconds: float
    ) -> None:
        """주기적으로 실행할 async 함수 등록.

        Args:
            func: 매 tick 마다 호출될 async 함수.
            interval_seconds: 호출 간격 (초).
        """
        ...

    async def start(self) -> None:
        """스케줄러 시작 (lifespan startup 에서 호출)."""
        ...

    async def stop(self) -> None:
        """스케줄러 정지 (lifespan shutdown 에서 호출)."""
        ...
