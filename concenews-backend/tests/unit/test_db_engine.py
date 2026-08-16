"""get_engine() DB 연결 timeout 설정 검증."""

from unittest.mock import MagicMock

from src.shared_kernel.db import engine as engine_module


class TestGetEngine:
    """DB 가 응답하지 않을 때 무제한 대기하지 않는 계약.

    get_engine 의 lru_cache 정리는 tests/conftest.py 의 전역 autouse
    fixture(_clear_test_state)가 매 test 후 수행한다.
    """

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
        assert connect_args.get("connect_timeout") == (
            engine_module.CONNECT_TIMEOUT_SECONDS
        )
