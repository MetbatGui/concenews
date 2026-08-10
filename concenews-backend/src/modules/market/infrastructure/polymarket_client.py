"""Polymarket Gamma API 클라이언트 (httpx.AsyncClient + asyncio.gather).

`GET /markets` 페이지네이션 (100 × 최대 5) → 500 마켓.
`GET /markets/{condition_id}/tags` 병렬 조회.

Rate limit: 4,000 req/10s (전체), 300 req/10s (/markets).
스파이크 실측: 50 병렬 콜 = 0.61초. 500 병렬도 리밋 하회.
"""
import asyncio
import json
from datetime import datetime

import httpx

from src.modules.market.domain.models import MarketMetadata, MarketSnapshotPayload, Tag


BASE_URL = "https://gamma-api.polymarket.com"
PAGE_SIZE = 100
MAX_PAGES = 5


class PolymarketGammaClient:
    """Polymarket Gamma API async 클라이언트.

    Attributes:
        _client: httpx.AsyncClient 인스턴스 (테스트 시 MockTransport 주입 가능).
    """

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        """Initialize.

        Args:
            client: 외부 주입 클라이언트 (테스트 용). None 이면 기본 생성.
        """
        self._client = client or httpx.AsyncClient(
            base_url=BASE_URL, timeout=httpx.Timeout(10.0)
        )

    async def aclose(self) -> None:
        """내부 HTTP 연결 풀을 명시적으로 종료한다."""
        await self._client.aclose()

    async def fetch_active_markets(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketMetadata]:
        """활성 마켓 목록 fetch (페이지네이션).

        Args:
            limit: 총 원하는 마켓 수 (100 단위로 페이지네이션).
            order: 정렬 기준 (예: "volume24hr").
            ascending: 오름차순 여부.

        Returns:
            MarketMetadata 리스트 (최대 limit 개).
        """
        num_pages = min((limit + PAGE_SIZE - 1) // PAGE_SIZE, MAX_PAGES)
        results: list[MarketMetadata] = []

        for page in range(num_pages):
            offset = page * PAGE_SIZE
            resp = await self._client.get(
                f"{BASE_URL}/markets",
                params={
                    "limit": PAGE_SIZE,
                    "offset": offset,
                    "active": "true",
                    "order": order,
                    "ascending": "true" if ascending else "false",
                },
            )
            resp.raise_for_status()
            try:
                batch = resp.json()
            except ValueError:
                break
            if not isinstance(batch, list) or not batch:
                break
            for m in batch:
                parsed = _parse_market(m)
                if parsed is not None:
                    results.append(parsed)
            if len(batch) < PAGE_SIZE:
                break

        return results

    async def fetch_tags_bulk(
        self, condition_ids: list[str]
    ) -> dict[str, list[Tag]]:
        """마켓별 태그 병렬 조회.

        Args:
            condition_ids: 조회할 condition ID 목록.

        Returns:
            condition_id → 태그 리스트 매핑.
            404 또는 예외 발생 시 해당 cid 는 빈 리스트 (부분 성공 허용).
        """
        if not condition_ids:
            return {}
        tasks = [self._fetch_tags(cid) for cid in condition_ids]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            cid: (r if isinstance(r, list) else [])
            for cid, r in zip(condition_ids, raw_results)
        }

    async def fetch_active_market_snapshots(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketSnapshotPayload]:
        """활성 마켓 응답을 스냅샷 후보 값 객체로 변환해 조회한다."""
        num_pages = min((limit + PAGE_SIZE - 1) // PAGE_SIZE, MAX_PAGES)
        results: list[MarketSnapshotPayload] = []

        for page in range(num_pages):
            batch = await self._fetch_market_page(page, order, ascending)
            if batch is None or not batch:
                break
            for market in batch:
                parsed = _parse_snapshot_payload(market)
                if parsed is not None:
                    results.append(parsed)
            if len(batch) < PAGE_SIZE:
                break

        return results

    async def _fetch_market_page(
        self, page: int, order: str, ascending: bool
    ) -> list[dict] | None:
        """한 페이지의 활성 마켓 원본 응답을 조회한다."""
        resp = await self._client.get(
            f"{BASE_URL}/markets",
            params={
                "limit": PAGE_SIZE,
                "offset": page * PAGE_SIZE,
                "active": "true",
                "order": order,
                "ascending": "true" if ascending else "false",
            },
        )
        resp.raise_for_status()
        try:
            batch = resp.json()
        except ValueError:
            return None
        return batch if isinstance(batch, list) else None

    async def _fetch_tags(self, condition_id: str) -> list[Tag]:
        """단일 마켓 태그 조회. 404/error 시 빈 리스트."""
        resp = await self._client.get(
            f"{BASE_URL}/markets/{condition_id}/tags"
        )
        if resp.status_code != 200:
            return []
        try:
            raw = resp.json()
        except ValueError:
            return []
        if not isinstance(raw, list):
            return []
        parsed = [_parse_tag(t) for t in raw]
        return [t for t in parsed if t is not None]


def _parse_market(raw: dict) -> MarketMetadata | None:
    """Raw dict → MarketMetadata. 필수 필드 부재/파싱 실패 시 None (skip)."""
    end_iso = raw.get("endDate") or raw.get("endDateIso")
    market_id = raw.get("id")
    if not end_iso or market_id is None:
        return None
    try:
        end_date = _parse_iso_datetime(end_iso)
    except ValueError:
        return None
    return MarketMetadata(
        condition_id=str(market_id),
        question=raw.get("question", ""),
        end_date=end_date,
    )


def _parse_snapshot_payload(raw: object) -> MarketSnapshotPayload | None:
    """Gamma 원본 마켓 응답을 스냅샷 후보 값 객체로 변환한다."""
    if not isinstance(raw, dict):
        return None
    market_id = raw.get("id")
    end_iso = raw.get("endDate") or raw.get("endDateIso")
    if market_id is None or not end_iso:
        return None
    try:
        return MarketSnapshotPayload(
            market_id=str(market_id),
            question=raw.get("question", ""),
            outcomes=_parse_string_array(raw.get("outcomes")),
            outcome_prices=_parse_float_array(raw.get("outcomePrices")),
            last_price=_parse_optional_float(raw.get("lastTradePrice")),
            best_bid=_parse_optional_float(raw.get("bestBid")),
            best_ask=_parse_optional_float(raw.get("bestAsk")),
            spread=_parse_optional_float(raw.get("spread")),
            liquidity=_parse_optional_float(raw.get("liquidity")),
            volume_24h=_parse_optional_float(raw.get("volume24hr")),
            volume_1w=_parse_optional_float(raw.get("volume1wk")),
            volume_1m=_parse_optional_float(raw.get("volume1mo")),
            end_date=_parse_iso_datetime(end_iso),
            active=bool(raw.get("active")),
            closed=bool(raw.get("closed")),
        )
    except (TypeError, ValueError):
        return None


def _parse_string_array(value: object) -> tuple[str, ...]:
    """Gamma의 JSON 문자열 배열 또는 배열을 문자열 tuple로 변환한다."""
    parsed = json.loads(value) if isinstance(value, str) else value
    if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
        raise ValueError("문자열 배열이 필요합니다.")
    return tuple(item for item in parsed if isinstance(item, str))


def _parse_float_array(value: object) -> tuple[float, ...]:
    """Gamma의 JSON 문자열 배열 또는 배열을 float tuple로 변환한다."""
    parsed = json.loads(value) if isinstance(value, str) else value
    if not isinstance(parsed, list):
        raise ValueError("숫자 배열이 필요합니다.")
    if not all(isinstance(item, (str, int, float)) for item in parsed):
        raise ValueError("숫자 배열이 필요합니다.")
    return tuple(
        float(item) for item in parsed if isinstance(item, (str, int, float))
    )


def _parse_optional_float(value: object) -> float | None:
    """nullable Gamma 숫자 필드를 float 또는 None으로 변환한다."""
    if value is None:
        return None
    if not isinstance(value, (str, int, float)):
        raise ValueError("숫자 또는 null이 필요합니다.")
    return float(value)


def _parse_tag(raw: dict) -> Tag | None:
    """Raw dict → Tag. id 부재/파싱 실패 시 None (skip)."""
    tag_id = raw.get("id")
    if tag_id is None:
        return None
    try:
        parsed_id = int(tag_id)
    except (TypeError, ValueError):
        return None
    return Tag(
        id=parsed_id,
        label=raw.get("label", ""),
        slug=raw.get("slug", ""),
    )


def _parse_iso_datetime(iso: str) -> datetime:
    """ISO 8601 (Z suffix 지원) → aware datetime."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))
