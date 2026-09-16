"""Unit test — KalshiMarketClient 스텁 계약."""
import pytest

from src.modules.market.infrastructure.kalshi_client import KalshiMarketClient


class TestKalshiMarketClientStub:
    """Walking Skeleton 스텁: 하드코딩 빈 응답."""

    @pytest.mark.asyncio
    async def test_fetch_active_markets_returns_empty_list(self):
        """Given: KalshiMarketClient 스텁
        When: fetch_active_markets()
        Then: 빈 리스트 반환 (실 HTTP 구현 전).
        """
        client = KalshiMarketClient()
        result = await client.fetch_active_markets(limit=500)
        assert result == []

    @pytest.mark.asyncio
    async def test_fetch_categories_bulk_returns_empty_dict(self):
        """Given: KalshiMarketClient 스텁
        When: fetch_categories_bulk()
        Then: 빈 dict 반환 (실 HTTP 구현 전).
        """
        client = KalshiMarketClient()
        result = await client.fetch_categories_bulk(series_ids=["KXFEDDECISION"])
        assert result == {}
