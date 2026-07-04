"""News API application."""
from fastapi import FastAPI

from src.modules.news.public import GetNewsResponse

app = FastAPI(
    title="Concenews API",
    version="0.1.0",
    description="Portfolio: 금리/통화 뉴스 조회 및 마켓 데이터 매칭 플랫폼",
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/news", response_model=GetNewsResponse)
def get_news() -> GetNewsResponse:
    """Walking skeleton stub. Wire-up PR 에서 Service 연결."""
    return GetNewsResponse(news=[], count=0)
