"""News 모듈 FastAPI router."""
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends

from src.modules.news.application.services import NewsService
from src.modules.news.infrastructure.repositories import InMemoryNewsRepository
from src.modules.news.presentation.schemas import (
    GetNewsRequest,
    GetNewsResponse,
    NewsItemResponse,
)

router = APIRouter(tags=["news"])


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


@router.get("/news", response_model=GetNewsResponse)
def get_news(
    request: Annotated[GetNewsRequest, Depends()],
    service: Annotated[NewsService, Depends(get_service)],
) -> GetNewsResponse:
    """뉴스 목록 조회.

    Args:
        request: 요청 파라미터 (limit).
        service: NewsService (Depends 주입).

    Returns:
        정렬된 뉴스 리스트 + count.
    """
    items = service.fetch_news(limit=request.limit)
    news = [NewsItemResponse.model_validate(item, from_attributes=True) for item in items]
    return GetNewsResponse(news=news, count=len(news))
