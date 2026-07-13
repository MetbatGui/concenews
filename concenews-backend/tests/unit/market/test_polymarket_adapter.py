"""Unit test — PolymarketGammaClient (httpx.AsyncClient + asyncio.gather).

httpx.MockTransport 로 응답 mock, 실제 HTTP 없이 검증.
"""
import json
from typing import Any

import httpx
import pytest

from src.modules.market.infrastructure.polymarket_client import PolymarketGammaClient


def _mock_transport(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def _market_json(mid: str, question: str, end_iso: str) -> dict[str, Any]:
    return {
        "id": mid,
        "question": question,
        "endDate": end_iso,
    }


class TestFetchActiveMarkets:
    """fetch_active_markets: 페이지네이션 + 응답 파싱."""

    @pytest.mark.asyncio
    async def test_paginates_across_five_pages(self):
        """Given: 5 페이지 각 100개 응답
        When: fetch_active_markets(limit=500)
        Then: 500 마켓 반환 + offset 0,100,200,300,400 호출.
        """
        offsets_seen: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            offset = int(request.url.params.get("offset", "0"))
            offsets_seen.append(offset)
            page = [
                _market_json(f"m{offset + i}", f"Q{i}", "2027-01-01T00:00:00Z")
                for i in range(100)
            ]
            return httpx.Response(200, json=page)

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_active_markets(
                limit=500, order="volume24hr", ascending=False
            )

        assert len(result) == 500
        assert offsets_seen == [0, 100, 200, 300, 400]

    @pytest.mark.asyncio
    async def test_parses_market_fields(self):
        """Given: 응답 dict
        When: fetch_active_markets
        Then: MarketMetadata 변환 (condition_id, question, end_date).
        """
        def handler(request: httpx.Request) -> httpx.Response:
            offset = int(request.url.params.get("offset", "0"))
            if offset > 0:
                return httpx.Response(200, json=[])
            return httpx.Response(
                200,
                json=[_market_json("2874512", "Will Fed cut rates?", "2027-01-01T00:00:00Z")],
            )

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_active_markets(
                limit=500, order="volume24hr", ascending=False
            )

        assert len(result) == 1
        m = result[0]
        assert m.condition_id == "2874512"
        assert m.question == "Will Fed cut rates?"
        assert m.end_date.isoformat().startswith("2027-01-01")

    @pytest.mark.asyncio
    async def test_stops_early_on_empty_page(self):
        """Given: 2번째 페이지가 빈 응답
        When: fetch_active_markets
        Then: 3페이지 이후 호출 안 함.
        """
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return httpx.Response(
                    200, json=[_market_json("m1", "Q", "2027-01-01T00:00:00Z")]
                )
            return httpx.Response(200, json=[])

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_active_markets(
                limit=500, order="volume24hr", ascending=False
            )

        assert len(result) == 1
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_sends_correct_query_params(self):
        """Given: 호출 파라미터
        When: fetch_active_markets(order="volume24hr", ascending=False)
        Then: active=true, order, ascending 전달됨.
        """
        captured: dict[str, str] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            captured.update(dict(request.url.params))
            return httpx.Response(200, json=[])

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            await adapter.fetch_active_markets(
                limit=500, order="volume24hr", ascending=False
            )

        assert captured["active"] == "true"
        assert captured["order"] == "volume24hr"
        assert captured["ascending"] == "false"
        assert captured["limit"] == "100"


class TestFetchTagsBulk:
    """fetch_tags_bulk: 병렬 태그 조회."""

    @pytest.mark.asyncio
    async def test_returns_tag_map_for_each_id(self):
        """Given: 3 condition_ids, 각각 태그 응답
        When: fetch_tags_bulk
        Then: {cid → tags} 매핑 반환.
        """
        def handler(request: httpx.Request) -> httpx.Response:
            cid = request.url.path.split("/")[-2]  # /markets/{cid}/tags
            return httpx.Response(
                200, json=[{"id": 159, "label": "Fed", "slug": "fed"}]
            )

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_tags_bulk(["m1", "m2", "m3"])

        assert set(result.keys()) == {"m1", "m2", "m3"}
        for tags in result.values():
            assert len(tags) == 1
            assert tags[0].id == 159
            assert tags[0].label == "Fed"

    @pytest.mark.asyncio
    async def test_empty_ids_returns_empty_dict(self):
        """Given: 빈 condition_ids
        When: fetch_tags_bulk
        Then: 빈 dict, HTTP 호출 없음.
        """
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(200, json=[])

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_tags_bulk([])

        assert result == {}
        assert call_count == 0

    @pytest.mark.asyncio
    async def test_handles_404_as_empty_tags(self):
        """Given: 마켓 하나가 404
        When: fetch_tags_bulk
        Then: 그 cid는 빈 리스트, 다른 것은 정상.
        """
        def handler(request: httpx.Request) -> httpx.Response:
            cid = request.url.path.split("/")[-2]
            if cid == "missing":
                return httpx.Response(404, text="not found")
            return httpx.Response(
                200, json=[{"id": 235, "label": "Bitcoin", "slug": "bitcoin"}]
            )

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_tags_bulk(["ok1", "missing", "ok2"])

        assert result["missing"] == []
        assert len(result["ok1"]) == 1
        assert len(result["ok2"]) == 1
