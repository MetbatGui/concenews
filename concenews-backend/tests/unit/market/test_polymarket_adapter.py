"""Unit test — PolymarketGammaClient (httpx.AsyncClient + asyncio.gather).

httpx.MockTransport 로 응답 mock, 실제 HTTP 없이 검증.
"""
from typing import Any

import httpx
import pytest

from src.modules.market.infrastructure.polymarket_client import PolymarketGammaClient
from tests.fixtures.polymarket import GAMMA_MARKET_SNAPSHOT


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


class TestPolymarketGammaClientLifecycle:
    """Polymarket HTTP 클라이언트의 자원 종료 계약."""

    @pytest.mark.asyncio
    async def test_aclose_closes_injected_http_client(self):
        """명시적 종료가 내부 HTTP 연결 풀을 닫는다."""
        client = httpx.AsyncClient()
        adapter = PolymarketGammaClient(client=client)

        await adapter.aclose()

        assert client.is_closed

    @pytest.mark.asyncio
    async def test_stops_early_on_incomplete_page(self):
        """Given: 1st 페이지 100개, 2nd 페이지 50개 (< PAGE_SIZE)
        When: fetch_active_markets
        Then: 3번째 페이지 호출 안 함 (조기 종료).
        """
        call_count = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                page = [
                    _market_json(f"m{i}", "Q", "2027-01-01T00:00:00Z")
                    for i in range(100)
                ]
            elif call_count == 2:
                page = [
                    _market_json(f"m{100 + i}", "Q", "2027-01-01T00:00:00Z")
                    for i in range(50)
                ]
            else:
                page = []
            return httpx.Response(200, json=page)

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_active_markets(
                limit=500, order="volume24hr", ascending=False
            )

        assert len(result) == 150
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


class TestFetchActiveMarketSnapshots:
    """fetch_active_market_snapshots: Spike fixture 기반 변환 계약."""

    @pytest.mark.asyncio
    async def test_parses_snapshot_fields_from_gamma_fixture(self):
        """Given: Gamma API 실제 형식의 JSON 문자열 배열 fixture
        When: fetch_active_market_snapshots(limit=200)
        Then: 배열·숫자·상태 필드가 값 객체로 변환된다.
        """
        offsets_seen: list[int] = []

        def handler(request: httpx.Request) -> httpx.Response:
            offset = int(request.url.params.get("offset", "0"))
            offsets_seen.append(offset)
            return httpx.Response(
                200, json=[GAMMA_MARKET_SNAPSHOT] if offset == 0 else []
            )

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_active_market_snapshots(
                limit=200, order="volume24hr", ascending=False
            )

        assert offsets_seen == [0]
        assert len(result) == 1
        snapshot = result[0]
        assert snapshot.market_id == "3438892"
        assert snapshot.outcomes == ("예", "아니오")
        assert snapshot.outcome_prices == (0.62, 0.38)
        assert snapshot.volume_24h == 8000.0
        assert snapshot.end_date.isoformat().startswith("2026-09-01")

    @pytest.mark.asyncio
    async def test_skips_invalid_snapshot_payload(self):
        """Given: 결과별 확률이 범위를 벗어난 Gamma 응답
        When: fetch_active_market_snapshots
        Then: 잘못된 후보를 저장 대상에서 제외한다.
        """
        invalid = {**GAMMA_MARKET_SNAPSHOT, "outcomePrices": '["1.2", "-0.2"]'}

        def handler(request: httpx.Request) -> httpx.Response:
            del request
            return httpx.Response(200, json=[invalid])

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_active_market_snapshots(
                limit=200, order="volume24hr", ascending=False
            )

        assert result == []

    @pytest.mark.asyncio
    async def test_skips_non_object_entry_without_stopping_page(self):
        """Given: 객체가 아닌 항목과 정상 Gamma 마켓이 섞인 응답
        When: fetch_active_market_snapshots
        Then: 잘못된 항목만 건너뛰고 정상 후보는 반환한다.
        """
        def handler(request: httpx.Request) -> httpx.Response:
            del request
            return httpx.Response(200, json=["invalid", GAMMA_MARKET_SNAPSHOT])

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_active_market_snapshots(
                limit=200, order="volume24hr", ascending=False
            )

        assert [snapshot.market_id for snapshot in result] == ["3438892"]


class TestParseMarketSkipsInvalid:
    """_parse_market: 필수 필드 부재/파싱 실패 시 skip."""

    @pytest.mark.asyncio
    async def test_market_without_end_date_is_skipped(self):
        """Given: endDate 없는 마켓 1개 + 정상 마켓 1개
        When: fetch_active_markets
        Then: 정상 마켓만 반환.
        """
        def handler(request: httpx.Request) -> httpx.Response:
            offset = int(request.url.params.get("offset", "0"))
            if offset > 0:
                return httpx.Response(200, json=[])
            return httpx.Response(
                200,
                json=[
                    {"id": "no_date", "question": "Q1"},  # endDate 누락
                    _market_json("2874512", "Q2", "2027-01-01T00:00:00Z"),
                ],
            )

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_active_markets(
                limit=500, order="volume24hr", ascending=False
            )

        assert len(result) == 1
        assert result[0].condition_id == "2874512"

    @pytest.mark.asyncio
    async def test_market_with_invalid_iso_is_skipped(self):
        """Given: endDate 가 유효하지 않은 ISO
        When: fetch_active_markets
        Then: skip (ValueError 로 크래시 X).
        """
        def handler(request: httpx.Request) -> httpx.Response:
            offset = int(request.url.params.get("offset", "0"))
            if offset > 0:
                return httpx.Response(200, json=[])
            return httpx.Response(
                200,
                json=[{"id": "bad", "question": "Q", "endDate": "not-a-date"}],
            )

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_active_markets(
                limit=500, order="volume24hr", ascending=False
            )

        assert result == []


class TestFetchTagsBulk:
    """fetch_tags_bulk: 병렬 태그 조회."""

    @pytest.mark.asyncio
    async def test_returns_tag_map_for_each_id(self):
        """Given: 3 condition_ids, 각각 태그 응답
        When: fetch_tags_bulk
        Then: {cid → tags} 매핑 반환.
        """
        def handler(request: httpx.Request) -> httpx.Response:
            del request
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
    async def test_gather_exception_yields_empty_tags(self):
        """Given: 하나의 요청이 network exception
        When: fetch_tags_bulk
        Then: 해당 cid 는 빈 리스트, 다른 것은 정상 (부분 성공).
        """
        def handler(request: httpx.Request) -> httpx.Response:
            cid = request.url.path.split("/")[-2]
            if cid == "broken":
                raise httpx.ConnectError("simulated network failure")
            return httpx.Response(
                200, json=[{"id": 235, "label": "Bitcoin", "slug": "bitcoin"}]
            )

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_tags_bulk(["ok", "broken"])

        assert result["broken"] == []
        assert len(result["ok"]) == 1

    @pytest.mark.asyncio
    async def test_malformed_tag_response_skips_invalid_entries(self):
        """Given: 태그 응답에 id 누락/비정수 항목 섞임
        When: fetch_tags_bulk
        Then: 유효한 태그만 반환, 크래시 X.
        """
        def handler(request: httpx.Request) -> httpx.Response:
            del request
            return httpx.Response(
                200,
                json=[
                    {"label": "no-id", "slug": "no-id"},           # id 누락
                    {"id": "not-a-number", "label": "bad"},        # 비정수
                    {"id": 159, "label": "Fed", "slug": "fed"},    # 정상
                ],
            )

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_tags_bulk(["m1"])

        assert len(result["m1"]) == 1
        assert result["m1"][0].id == 159

    @pytest.mark.asyncio
    async def test_non_json_tag_response_yields_empty(self):
        """Given: 200 이지만 body 가 JSON 이 아님
        When: fetch_tags_bulk
        Then: 해당 cid 빈 리스트, 크래시 X.
        """
        def handler(request: httpx.Request) -> httpx.Response:
            del request
            return httpx.Response(200, text="not json")

        async with httpx.AsyncClient(transport=_mock_transport(handler)) as client:
            adapter = PolymarketGammaClient(client=client)
            result = await adapter.fetch_tags_bulk(["m1"])

        assert result["m1"] == []

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
