"""News 모듈 FastAPI router."""
from typing import Annotated

from fastapi import APIRouter, Depends

from src.modules.news.application.services import NewsService
from src.modules.news.bootstrap import get_service
from src.modules.news.presentation.schemas import (
    GetNewsRequest,
    GetNewsResponse,
    NewsItemResponse,
)

router = APIRouter(tags=["news"])


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
    news = [NewsItemResponse.model_validate(item.model_dump()) for item in items]
    return GetNewsResponse(news=news, count=len(news))
