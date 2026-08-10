"""stdlib asyncio 기반 공용 Scheduler adapter."""
import asyncio
import logging
from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


class AsyncioSchedulerAdapter:
    """이름 있는 비동기 주기 작업을 실행한다.

    각 작업의 예외를 격리해 다른 작업과 다음 실행 주기를 보존한다.
    """

    def __init__(self) -> None:
        """빈 Scheduler를 초기화한다."""
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._jobs: dict[str, tuple[Callable[[], Awaitable[None]], float]] = {}
        self._running = False

    @property
    def job_intervals(self) -> dict[str, float]:
        """등록 작업명과 실행 주기 사본을 반환한다."""
        return {name: interval for name, (_, interval) in self._jobs.items()}

    def schedule(
        self,
        name: str,
        func: Callable[[], Awaitable[None]],
        interval_seconds: float,
    ) -> None:
        """이름 있는 async 작업을 등록한다.

        Args:
            name: 로그와 lifecycle에 사용할 고유 작업명.
            func: 매 tick마다 실행할 async 함수.
            interval_seconds: 호출 간격(초).

        Raises:
            ValueError: 이름이 중복되거나 주기가 양수가 아닌 경우.
        """
        if name in self._jobs:
            raise ValueError(f"이미 등록된 작업: {name}")
        if interval_seconds <= 0:
            raise ValueError("실행 주기는 양수여야 함")
        self._jobs[name] = (func, interval_seconds)

    async def start(self) -> None:
        """등록된 모든 작업의 주기 실행을 시작한다."""
        if self._running:
            raise RuntimeError("Scheduler가 이미 시작되었습니다.")
        self._running = True
        for name, (func, interval) in self._jobs.items():
            self._tasks[name] = asyncio.create_task(
                self._run_periodic(name, func, interval), name=name
            )

    async def stop(self) -> None:
        """등록 작업을 취소하고 종료한다."""
        self._running = False
        for task in self._tasks.values():
            task.cancel()
        for task in self._tasks.values():
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()

    async def trigger_all(self) -> None:
        """등록된 모든 작업을 한 번씩 실행한다."""
        for name, (func, _) in self._jobs.items():
            await self._run_job(name, func)

    async def _run_periodic(
        self, name: str, func: Callable[[], Awaitable[None]], interval: float
    ) -> None:
        """작업 하나를 주기적으로 실행한다."""
        while self._running:
            await self._run_job(name, func)
            await asyncio.sleep(interval)

    async def _run_job(
        self, name: str, func: Callable[[], Awaitable[None]]
    ) -> None:
        """작업 예외를 격리하고 이름과 함께 기록한다."""
        try:
            await func()
        except Exception:
            logger.exception("Scheduler 작업 실패: %s", name)
