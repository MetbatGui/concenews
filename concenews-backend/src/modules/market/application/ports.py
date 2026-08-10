"""Application ports (Protocol interfaces).

Domain 계층이 의존하는 외부 접점 정의.
Infrastructure 구현체는 이 Protocol을 만족.
"""
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.modules.market.domain.models import (
    MarketClassification,
    MarketMetadata,
    MarketSnapshot,
    MarketSnapshotPayload,
    Tag,
)


class MarketSourcePort(Protocol):
    """Polymarket 마켓 데이터 소스."""

    async def fetch_active_markets(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketMetadata]:
        """활성 마켓 목록 fetch.

        Args:
            limit: 페이지당 개수.
            order: 정렬 기준 필드명.
            ascending: 오름차순 여부.

        Returns:
            MarketMetadata 리스트.
        """
        ...

    async def fetch_tags_bulk(
        self, condition_ids: list[str]
    ) -> dict[str, list[Tag]]:
        """마켓별 태그 병렬 조회.

        Args:
            condition_ids: 조회할 condition ID 목록.

        Returns:
            condition_id → 태그 리스트 매핑.
        """
        ...

    async def fetch_active_market_snapshots(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketSnapshotPayload]:
        """스냅샷 후보가 될 활성 마켓 원본을 조회한다."""
        ...


class ClassificationRepositoryPort(Protocol):
    """분류 결과 저장소."""

    def find_active_condition_ids(self, now: datetime) -> set[str]:
        """유효 캐시 (end_date > now)의 condition_id 집합.

        Args:
            now: 현재 시각 (UTC).

        Returns:
            유효한 분류 캐시의 condition_id 집합.
        """
        ...

    def save_bulk(self, classifications: list[MarketClassification]) -> None:
        """분류 결과 일괄 저장.

        Args:
            classifications: 저장할 분류 결과 리스트.
        """
        ...

    def find_active_macro_condition_ids(self, now: datetime) -> set[str]:
        """유효한 MACRO 분류의 시장 식별자만 조회한다."""
        ...


class SnapshotRepositoryPort(Protocol):
    """마켓 스냅샷 저장소."""

    def save_bulk(self, snapshots: list[MarketSnapshot]) -> None:
        """스냅샷을 한 번에 저장한다.

        Args:
            snapshots: 저장할 스냅샷 목록.
        """
        ...


class SnapshotIdGeneratorPort(Protocol):
    """마켓 스냅샷 식별자 발급기."""

    def generate(self) -> UUID:
        """새 스냅샷 UUID를 발급한다."""
        ...
