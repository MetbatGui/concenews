"""외부 경계 없이 Scheduler 컨테이너 lifecycle을 검증하는 진입점."""
import asyncio
import os
from pathlib import Path

from src.scheduler_main import run_scheduler
from src.shared_kernel.scheduler import AsyncioSchedulerAdapter


class SmokeScheduler(AsyncioSchedulerAdapter):
    """두 작업 등록과 시작 완료를 readiness 파일로 알리는 Scheduler."""

    def __init__(self, readiness_file: Path) -> None:
        super().__init__()
        self._readiness_file = readiness_file

    async def start(self) -> None:
        """작업을 시작한 뒤 readiness 파일을 생성한다."""
        await super().start()
        self._readiness_file.touch()


async def _noop_job() -> None:
    """외부 API·DB 접근 없이 Scheduler 등록만 검증한다."""


def main() -> None:
    """Fake 작업 두 개를 등록한 Scheduler lifecycle을 실행한다."""
    readiness_file = Path(os.environ["SCHEDULER_SMOKE_READY_FILE"])
    scheduler = SmokeScheduler(readiness_file)
    scheduler.schedule("news_collector", _noop_job, interval_seconds=3600)
    scheduler.schedule("market_classifier", _noop_job, interval_seconds=3600)
    asyncio.run(run_scheduler(scheduler=scheduler))


if __name__ == "__main__":
    main()
