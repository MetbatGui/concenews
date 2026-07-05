"""News API application."""
from fastapi import FastAPI

from src.modules.news.public import router as news_router
from src.shared_kernel.db.settings import load_config

load_config()

app = FastAPI(
    title="Concenews API",
    version="0.1.0",
    description="Portfolio: 금리/통화 뉴스 조회 및 마켓 데이터 매칭 플랫폼",
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


app.include_router(news_router)
