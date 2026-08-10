"""Scheduler 독립 진입점과 API 실행 경계 테스트."""
import asyncio
import signal

from fastapi.testclient import TestClient
import pytest

import src.main as api_main
from src import scheduler_main


class _FakeScheduler:
    """Scheduler lifecycle 호출을 관찰하는 Fake."""

    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


class TestApiRuntimeBoundary:
    """API 프로세스는 Scheduler를 소유하지 않는다."""

    def test_api_lifespan_does_not_start_scheduler(self):
        """API 기동은 Scheduler 조립 함수를 호출하지 않는다."""
        assert not hasattr(api_main, "setup_news_collector")

        with TestClient(api_main.app) as client:
            assert client.get("/health").json() == {"status": "ok"}


class TestSchedulerEntrypoint:
    """독립 Scheduler 프로세스의 조립과 종료 계약."""

    def test_build_scheduler_registers_both_jobs(self, monkeypatch):
        """하나의 Scheduler에 뉴스와 마켓 작업을 모두 등록한다."""
        scheduler = _FakeScheduler()
        registered: list[str] = []

        monkeypatch.setattr(scheduler_main, "AsyncioSchedulerAdapter", lambda: scheduler)
        monkeypatch.setattr(
            scheduler_main,
            "register_news_collection_job",
            lambda target: registered.append("news") if target is scheduler else None,
        )
        monkeypatch.setattr(
            scheduler_main,
            "register_market_classifier_job",
            lambda target: registered.append("market") if target is scheduler else None,
        )

        assert scheduler_main.build_scheduler() is scheduler
        assert registered == ["news", "market"]

    def test_run_scheduler_stops_on_shutdown_signal(self):
        """종료 대기 완료 뒤 Scheduler를 항상 정리한다."""
        scheduler = _FakeScheduler()

        async def stop_immediately() -> None:
            return None

        asyncio.run(
            scheduler_main.run_scheduler(
                scheduler=scheduler,
                wait_for_shutdown=stop_immediately,
            )
        )

        assert scheduler.started
        assert scheduler.stopped

    @pytest.mark.asyncio
    async def test_wait_for_shutdown_returns_after_sigterm(self, monkeypatch):
        """SIGTERM handler가 종료 대기를 해제한다."""
        callbacks: dict[signal.Signals, object] = {}
        loop = asyncio.get_running_loop()

        monkeypatch.setattr(
            loop,
            "add_signal_handler",
            lambda shutdown_signal, callback: callbacks.__setitem__(
                shutdown_signal, callback
            ),
        )

        wait_task = asyncio.create_task(scheduler_main._wait_for_shutdown_signal())
        await asyncio.sleep(0)
        callback = callbacks[signal.SIGTERM]
        assert callable(callback)
        callback()
        await wait_task
