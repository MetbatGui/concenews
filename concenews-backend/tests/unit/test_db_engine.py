"""get_engine() DB 연결 timeout 설정 검증."""

from unittest.mock import MagicMock

import pytest

from src.shared_kernel.db import engine as engine_module


class TestGetEngine:
    """DB 가 응답하지 않을 때 무제한 대기하지 않는 계약."""

    @pytest.fixture(autouse=True)
    def _clear_engine_cache(self):
        """모듈 singleton 캐시가 테스트 간 새어나가지 않게 한다."""
        engine_module.get_engine.cache_clear()
        yield
        engine_module.get_engine.cache_clear()

    def test_passes_connect_timeout_to_create_engine(self, monkeypatch):
        """Given: DB 가 응답하지 않는 상황
        When: get_engine() 이 Engine 을 조립
        Then: connect_args 에 connect_timeout 이 포함되어 OS 기본 TCP
            타임아웃에 기대지 않는다.
        """
        captured: dict = {}

        def fake_create_engine(url, **kwargs):
            captured.update(kwargs)
            return MagicMock()

        monkeypatch.setattr(engine_module, "create_engine", fake_create_engine)

        engine_module.get_engine()

        connect_args = captured.get("connect_args", {})
        assert "connect_timeout" in connect_args
        assert 0 < connect_args["connect_timeout"] <= 10
