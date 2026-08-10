"""Polymarket Data API 참여자 보유 포지션 어댑터."""

import math

import httpx

from src.modules.market.domain.models import ParticipantPositionPayload


BASE_URL = "https://data-api.polymarket.com"


class PolymarketDataClient:
    """공개 Data API에서 결과별 상위 보유 포지션을 조회한다."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        """테스트 가능한 HTTP client를 받는다."""
        self._client = client or httpx.AsyncClient(
            base_url=BASE_URL, timeout=httpx.Timeout(10.0)
        )

    async def aclose(self) -> None:
        """HTTP 연결을 명시적으로 종료한다."""
        await self._client.aclose()

    async def fetch_top_holder_positions(
        self, condition_id: str, limit: int
    ) -> list[ParticipantPositionPayload]:
        """조건 ID의 결과별 상위 보유 포지션을 평탄화해 반환한다."""
        response = await self._client.get(
            f"{BASE_URL}/holders", params={"market": condition_id, "limit": limit}
        )
        response.raise_for_status()
        try:
            raw = response.json()
        except ValueError:
            return []
        if not isinstance(raw, list):
            return []

        positions: list[ParticipantPositionPayload] = []
        for token_result in raw:
            if not isinstance(token_result, dict):
                continue
            holders = token_result.get("holders")
            if not isinstance(holders, list):
                continue
            for holder in holders:
                payload = _parse_holder(holder)
                if payload is not None:
                    positions.append(payload)
        return positions


def _parse_holder(raw: object) -> ParticipantPositionPayload | None:
    """Data API 보유자 항목을 유효한 Domain payload로 변환한다."""
    if not isinstance(raw, dict):
        return None
    wallet = raw.get("proxyWallet")
    outcome_index = raw.get("outcomeIndex")
    amount = raw.get("amount")
    if (
        not isinstance(wallet, str)
        or not wallet
        or isinstance(outcome_index, bool)
        or not isinstance(outcome_index, int)
        or isinstance(amount, bool)
        or not isinstance(amount, (str, int, float))
    ):
        return None
    try:
        position_amount = float(amount)
    except ValueError:
        return None
    if not math.isfinite(position_amount):
        return None
    try:
        return ParticipantPositionPayload(
            wallet_address=wallet,
            outcome_index=outcome_index,
            position_amount=position_amount,
        )
    except ValueError:
        return None
