"""마켓 스냅샷 UUID v7 발급 어댑터."""
from uuid import UUID

from uuid_utils.compat import uuid7


class UuidV7SnapshotIdGenerator:
    """시간 정렬 가능한 UUID v7 스냅샷 식별자 발급기."""

    def generate(self) -> UUID:
        """새 UUID v7을 반환한다."""
        return uuid7()
