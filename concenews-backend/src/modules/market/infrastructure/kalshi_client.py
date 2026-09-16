"""Kalshi 마켓 데이터 소스 — Walking Skeleton 스텁.

실제 HTTP 구현은 후속 PR. 지금은 KalshiMarketSourcePort 계약만 만족하는
하드코딩 스텁이다. Integration test는 이 스텁이 아니라 Fake를 주입해
검증한다(Classicist 원칙 — 값 없는 스텁 자체는 검증 대상이 아니다).
"""

from src.modules.market.domain.models import KalshiMarketMetadata


class KalshiMarketClient:
    """KalshiMarketSourcePort 구현 — Walking Skeleton 스텁."""

    async def fetch_active_markets(self, limit: int) -> list[KalshiMarketMetadata]:
        """스텁: 항상 빈 리스트."""
        return []

    async def fetch_categories_bulk(self, series_ids: list[str]) -> dict[str, str]:
        """스텁: 항상 빈 dict."""
        return {}
