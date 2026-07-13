"""Polymarket Gamma API 클라이언트 (Walking Skeleton 스텁).

실제 httpx 기반 async 구현은 PR #4에서 완성.
현재: 하드코딩 응답 반환.
"""
from datetime import UTC, datetime, timedelta

from src.modules.market.domain.models import MarketMetadata, Tag


class PolymarketGammaClient:
    """Gamma API 클라이언트 (스텁 구현).

    PR #4에서 httpx.AsyncClient로 실제 구현.
    """

    async def fetch_active_markets(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketMetadata]:
        """활성 마켓 목록 (스텁: 빈 리스트).

        Args:
            limit: 페이지당 개수.
            order: 정렬 기준.
            ascending: 오름차순 여부.

        Returns:
            빈 리스트 (스텁).
        """
        del limit, order, ascending
        return []

    async def fetch_tags_bulk(
        self, condition_ids: list[str]
    ) -> dict[str, list[Tag]]:
        """마켓별 태그 조회 (스텁: 빈 dict).

        Args:
            condition_ids: 조회할 condition ID 목록.

        Returns:
            빈 dict (스텁).
        """
        del condition_ids
        return {}


def _stub_future_date() -> datetime:
    return datetime.now(UTC) + timedelta(days=30)
