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
