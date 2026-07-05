"""News 모듈 조립 (Composition Root).

Repository / Service / Endpoint 조합을 여기서 결정.
Layer 안쪽 (application, domain) 는 이 파일을 몰라도 됨.
Router 는 provider 함수만 참조 — Infrastructure 직접 import 금지.
"""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from .application.services import NewsService
from .infrastructure.repositories import InMemoryNewsRepository


@lru_cache(maxsize=1)
def get_repository() -> InMemoryNewsRepository:
    """Repository 싱글톤 provider.

    앱 수명 동안 하나의 InMemoryNewsRepository 인스턴스 공유.
    Test 에서는 app.dependency_overrides 로 교체.

    Returns:
        싱글톤 InMemoryNewsRepository.
    """
    return InMemoryNewsRepository()


def get_service(
    repository: Annotated[InMemoryNewsRepository, Depends(get_repository)],
) -> NewsService:
    """NewsService provider (Repository 주입).

    Args:
        repository: 저장소 (Depends 주입).

    Returns:
        NewsService 인스턴스.
    """
    return NewsService(repository=repository)
