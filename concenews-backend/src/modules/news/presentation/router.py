"""News 모듈 FastAPI router."""
from fastapi import APIRouter

from src.modules.news.presentation.schemas import GetNewsResponse

router = APIRouter(tags=["news"])


@router.get("/news", response_model=GetNewsResponse)
def get_news() -> GetNewsResponse:
    """뉴스 목록 조회.

    현재 stub 응답. 다음 단계에서 Service DI 연결.

    Returns:
        빈 뉴스 리스트 (walking skeleton).
    """
    return GetNewsResponse(news=[], count=0)
