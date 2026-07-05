"""News 모듈 identity 발급 impl.

Port: src/modules/news/application/ports.py (IdGenerator).
ADR: docs/decisions/2026-07-04-id-strategy.md
Rule of Three: 두 번째 모듈이 identity 발급 필요 시 shared_kernel 로 이전.
"""
from uuid import UUID

from uuid_utils.compat import uuid7


class UuidV7Generator:
    """UUID v7 (RFC 9562) 발급기.

    시간순 정렬 가능 (앞 48비트 timestamp) — PG 인덱스 friendly.
    Stateless: 인스턴스 상태 없음.

    Port 계약: src.modules.news.application.ports.IdGenerator.
    """

    def generate(self) -> UUID:
        """UUID v7 반환.

        Returns:
            stdlib uuid.UUID (version=7).
        """
        return uuid7()
