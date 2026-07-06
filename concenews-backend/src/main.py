"""News API application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.modules.news.bootstrap import setup_news_collector
from src.modules.news.public import router as news_router
from src.shared_kernel.db.settings import load_config

load_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: startup (scheduler) / shutdown.

    Yields:
        None (컨텍스트).
    """
    # startup
    try:
        scheduler, session = await setup_news_collector()
        app.state.scheduler = scheduler
        app.state.db_session = session

        await scheduler.start()
    except ValueError as e:
        raise RuntimeError(f"뉴스 수집기 초기화 실패: {e}") from e

    yield

    # shutdown
    await scheduler.stop()
    session.close()


app = FastAPI(
    title="Concenews API",
    version="0.1.0",
    description="Portfolio: 금리/통화 뉴스 조회 및 마켓 데이터 매칭 플랫폼",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


app.include_router(news_router)
