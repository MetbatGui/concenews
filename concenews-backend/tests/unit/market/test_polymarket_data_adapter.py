"""Polymarket Data API 참여자 어댑터 계약 테스트."""

import httpx
import pytest

from src.modules.market.infrastructure.polymarket_data_client import (
    PolymarketDataClient,
)
from tests.fixtures.polymarket import POLYMARKET_TOP_HOLDERS


class TestPolymarketDataClient:
    """Spike fixture 기반 상위 보유 포지션 변환 계약."""

    @pytest.mark.asyncio
    async def test_flattens_holders_for_each_outcome_token(self):
        """Given: 결과 token별 상위 보유자 fixture
        When: 상위 보유 포지션 조회
        Then: 원시 보유량과 결과 인덱스를 보존해 평탄화한다.
        """
        captured: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured.update(dict(request.url.params))
            return httpx.Response(200, json=POLYMARKET_TOP_HOLDERS)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            adapter = PolymarketDataClient(client=client)
            positions = await adapter.fetch_top_holder_positions("0xcondition", 20)

        assert captured == {"market": "0xcondition", "limit": "20"}
        assert [
            (item.wallet_address, item.outcome_index, item.position_amount)
            for item in positions
        ] == [
            ("0xwallet-yes", 0, 125.5),
            ("0xwallet-yes-2", 0, 10.0),
            ("0xwallet-no", 1, 75.25),
        ]

    @pytest.mark.asyncio
    async def test_skips_malformed_holder_without_dropping_valid_positions(self):
        """Given: 잘못된 항목과 유효 항목이 섞인 응답
        When: 상위 보유 포지션 조회
        Then: 유효한 관측값만 반환한다.
        """
        payload = [
            {
                "holders": [
                    {"proxyWallet": "0xok", "amount": 1, "outcomeIndex": 0},
                    {"proxyWallet": "0xbad", "amount": 0, "outcomeIndex": 0},
                ]
            }
        ]

        def handler(request: httpx.Request) -> httpx.Response:
            del request
            return httpx.Response(200, json=payload)

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            positions = await PolymarketDataClient(
                client=client
            ).fetch_top_holder_positions("0xcondition", 20)

        assert [item.wallet_address for item in positions] == ["0xok"]
