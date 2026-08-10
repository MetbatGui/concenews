"""뉴스 수집과 마켓 분류를 실행하는 Scheduler 프로세스 진입점."""
import asyncio
import logging
import signal
from collections.abc import Awaitable, Callable

from src.modules.market.bootstrap import (
    register_market_classifier_job,
    register_market_snapshot_job,
)
from src.modules.news.bootstrap import register_news_collection_job
from src.shared_kernel.scheduler import AsyncioSchedulerAdapter

logger = logging.getLogger(__name__)


def build_scheduler() -> AsyncioSchedulerAdapter:
    """두 주기 작업을 등록한 Scheduler를 조립한다."""
    scheduler = AsyncioSchedulerAdapter()
    register_news_collection_job(scheduler)
    register_market_classifier_job(scheduler)
    register_market_snapshot_job(scheduler)
    return scheduler


async def run_scheduler(
    scheduler: AsyncioSchedulerAdapter | None = None,
    wait_for_shutdown: Callable[[], Awaitable[None]] | None = None,
) -> None:
    """Scheduler를 시작하고 종료 신호가 오면 등록 작업을 정리한다.

    Args:
        scheduler: 테스트에서 주입할 Scheduler. 생략하면 운영 조립을 사용한다.
        wait_for_shutdown: 테스트용 종료 대기 함수. 생략하면 SIGTERM을 기다린다.
    """
    active_scheduler: AsyncioSchedulerAdapter | None = None
    try:
        stop_event = _install_shutdown_signal_handlers()
        active_scheduler = scheduler or build_scheduler()
        await active_scheduler.start()
        logger.info("Scheduler 작업을 시작했습니다.")

        if wait_for_shutdown is None:
            await stop_event.wait()
        else:
            await wait_for_shutdown()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt를 받아 Scheduler를 종료합니다.")
    finally:
        if active_scheduler is not None:
            await active_scheduler.stop()
            logger.info("Scheduler 작업을 정리했습니다.")


def _install_shutdown_signal_handlers() -> asyncio.Event:
    """SIGTERM 또는 SIGINT를 받을 종료 Event를 준비한다."""
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    for shutdown_signal in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(shutdown_signal, stop_event.set)
        except NotImplementedError:
            signal.signal(shutdown_signal, lambda *_: stop_event.set())

    return stop_event


def main() -> None:
    """Scheduler 프로세스를 실행한다."""
    asyncio.run(run_scheduler())


if __name__ == "__main__":
    main()
