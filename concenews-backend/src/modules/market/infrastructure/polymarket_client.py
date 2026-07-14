"""Polymarket Gamma API 클라이언트 (httpx.AsyncClient + asyncio.gather).

`GET /markets` 페이지네이션 (100 × 최대 5) → 500 마켓.
`GET /markets/{condition_id}/tags` 병렬 조회.

Rate limit: 4,000 req/10s (전체), 300 req/10s (/markets).
스파이크 실측: 50 병렬 콜 = 0.61초. 500 병렬도 리밋 하회.
"""
import asyncio
from datetime import datetime

import httpx

from src.modules.market.domain.models import MarketMetadata, Tag


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
            batch = resp.json()
            if not batch:
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

    async def _fetch_tags(self, condition_id: str) -> list[Tag]:
        """단일 마켓 태그 조회. 404/error 시 빈 리스트."""
        resp = await self._client.get(
            f"{BASE_URL}/markets/{condition_id}/tags"
        )
        if resp.status_code != 200:
            return []
        return [_parse_tag(t) for t in resp.json()]


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


def _parse_tag(raw: dict) -> Tag:
    """Raw dict → Tag."""
    return Tag(
        id=int(raw["id"]),
        label=raw.get("label", ""),
        slug=raw.get("slug", ""),
    )


def _parse_iso_datetime(iso: str) -> datetime:
    """ISO 8601 (Z suffix 지원) → aware datetime."""
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))
