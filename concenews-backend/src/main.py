"""News API application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.modules.news.bootstrap import setup_news_collector
from src.modules.news.public import router as news_router
from src.shared_kernel.db.settings import load_config

load_config()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: startup with retry (5x) / graceful shutdown.

    Yields:
        None (컨텍스트).
    """
    # startup with exponential backoff retry
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def setup_with_retry():
        return await setup_news_collector()

    scheduler = None
    try:
        scheduler = await setup_with_retry()
        app.state.scheduler = scheduler
        await scheduler.start()
        logger.info("뉴스 수집기 시작됨")
    except Exception as e:
        logger.error(f"뉴스 수집기 초기화 실패 (5회 재시도 후): {e}", exc_info=True)
        raise RuntimeError(f"뉴스 수집기 초기화 실패: {e}") from e

    yield

    # shutdown (graceful)
    if scheduler:
        try:
            await scheduler.stop()
            logger.info("뉴스 수집기 정지됨")
        except Exception as e:
            logger.error(f"뉴스 수집기 정지 중 오류: {e}", exc_info=True)


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
