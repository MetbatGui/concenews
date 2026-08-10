"""공용 Scheduler Runtime 단위 테스트."""
import pytest

from src.modules.market.bootstrap import register_market_classifier_job
from src.modules.news.bootstrap import register_news_collection_job
from src.shared_kernel.scheduler import AsyncioSchedulerAdapter


class TestAsyncioSchedulerAdapter:
    """공용 Scheduler의 관찰 가능한 실행 계약."""

    @pytest.mark.asyncio
    async def test_trigger_all_continues_after_one_job_fails(self, caplog):
        """Given: 실패 작업과 성공 작업이 등록된 Scheduler
        When: 모든 작업을 수동 실행
        Then: 성공 작업은 실행되고 실패는 작업명과 함께 기록된다.
        """
        executed: list[str] = []
        scheduler = AsyncioSchedulerAdapter()

        async def fail_job() -> None:
            raise RuntimeError("실패")

        async def success_job() -> None:
            executed.append("success")

        scheduler.schedule("fail", fail_job, interval_seconds=60)
        scheduler.schedule("success", success_job, interval_seconds=60)

        await scheduler.trigger_all()

        assert executed == ["success"]
        assert "fail" in caplog.text


class TestSchedulerJobRegistration:
    """뉴스·마켓 작업 조립 계약."""

    def test_registers_news_and_market_jobs_with_configured_intervals(
        self, monkeypatch
    ):
        """Given: 두 작업의 interval 환경 설정
        When: 공용 Scheduler에 뉴스와 마켓 작업을 등록
        Then: 이름과 interval이 관찰 가능한 등록 상태에 남는다.
        """
        monkeypatch.setenv("THENEWSAPI_TOKEN", "test-token")
        monkeypatch.setenv("NEWS_COLLECTOR_INTERVAL", "120")
        monkeypatch.setenv("MARKET_CLASSIFIER_INTERVAL", "300")
        scheduler = AsyncioSchedulerAdapter()

        register_news_collection_job(scheduler)
        register_market_classifier_job(scheduler)

        assert scheduler.job_intervals == {
            "news_collector": 120,
            "market_classifier": 300,
        }
