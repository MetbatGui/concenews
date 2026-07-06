"""뉴스 수집 스케줄러 adapter (infrastructure).

Asyncio 기반 스케줄러 (stdlib, plan 준수).
"""
import asyncio
from collections.abc import Awaitable, Callable


class AsyncioSchedulerAdapter:
    """Asyncio 기반 스케줄러.

    SchedulerPort 구현체. 주기적으로 async 함수 실행.

    상세: docs/decisions/2026-07-06-scheduler-choice.md
    """

    def __init__(self) -> None:
        """Initialize scheduler."""
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._jobs: list[tuple[Callable[[], Awaitable[None]], float]] = []
        self._running = False

    def schedule(
        self, func: Callable[[], Awaitable[None]], interval_seconds: float
    ) -> None:
        """주기적으로 실행할 async 함수 등록.

        Args:
            func: 매 tick 마다 호출될 async 함수.
            interval_seconds: 호출 간격 (초).
        """
        self._jobs.append((func, interval_seconds))

    async def start(self) -> None:
        """스케줄러 시작 (lifespan startup 에서 호출)."""
        self._running = True

        for i, (func, interval) in enumerate(self._jobs):
            task_name = f"job_{i}"
            task = asyncio.create_task(self._run_periodic(func, interval))
            self._tasks[task_name] = task

    async def stop(self) -> None:
        """스케줄러 정지 (lifespan shutdown 에서 호출)."""
        self._running = False

        for task in self._tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._tasks.clear()

    async def trigger_all(self) -> None:
        """모든 job 수동 트리거 (테스트용)."""
        for func, _ in self._jobs:
            await func()

    async def _run_periodic(
        self, func: Callable[[], Awaitable[None]], interval: float
    ) -> None:
        """Periodic task runner."""
        while self._running:
            try:
                await func()
            except Exception:
                # Log silently (나중에 로깅 추가)
                pass

            await asyncio.sleep(interval)
