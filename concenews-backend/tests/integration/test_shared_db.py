"""Shared kernel DB smoke test.

목적: engine + session 이 실 PG 에 연결 가능한지 형식적 검증.
로직 없는 wiring 이므로 unit test 없음.
상세: docs/decisions/2026-07-06-repository-strategy.md
"""
from sqlalchemy import text

from src.shared_kernel.db.session import get_session


def test_session_can_execute_select_one():
    """Session 이 실 PG 에 연결하여 SELECT 1 실행 가능.

    Given: docker-compose PG 실행 중
    When: get_session() 로 세션 획득, SELECT 1 실행
    Then: 결과값 1 반환
    """
    session_gen = get_session()
    session = next(session_gen)
    try:
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        try:
            next(session_gen)
        except StopIteration:
            pass
