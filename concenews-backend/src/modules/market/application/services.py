"""Application service — 마켓 분류 오케스트레이션.

Walking Skeleton: 최소 흐름 (fetch → classify → save).
실제 캐시 조회, 병렬 태그 fetch는 PR #5 (Service 실제 흐름)에서 완성.
"""
from datetime import UTC, datetime

from src.modules.market.application.ports import (
    ClassificationRepositoryPort,
    MarketSourcePort,
)
from src.modules.market.domain.classifier import classify
from src.modules.market.domain.models import MarketClassification


class MarketClassifierService:
    """Polymarket 마켓 분류 오케스트레이션."""

    def __init__(
        self,
        source: MarketSourcePort,
        repository: ClassificationRepositoryPort,
    ) -> None:
        """Initialize.

        Args:
            source: 마켓 데이터 소스.
            repository: 분류 저장소.
        """
        self._source = source
        self._repository = repository

    async def run(self) -> None:
        """1회 실행: fetch → classify → save.

        Walking Skeleton 흐름:
        1. 활성 마켓 목록 fetch
        2. 각 마켓의 태그 조회
        3. classify() 호출
        4. 결과 저장 (MACRO/NON_MACRO만)
        """
        now = datetime.now(UTC)
        cached_ids = self._repository.find_active_condition_ids(now)

        markets = await self._source.fetch_active_markets(
            limit=100, order="volume24hr", ascending=False
        )
        new_markets = [m for m in markets if m.condition_id not in cached_ids]

        if not new_markets:
            return

        tag_map = await self._source.fetch_tags_bulk(
            [m.condition_id for m in new_markets]
        )

        classifications: list[MarketClassification] = []
        for market in new_markets:
            tags = tag_map.get(market.condition_id, [])
            result = classify({t.id for t in tags})
            if result is None:
                continue
            classifications.append(
                MarketClassification(
                    condition_id=market.condition_id,
                    question=market.question,
                    classification=result,
                    tags=tuple(tags),
                    end_date=market.end_date,
                    classified_at=now,
                )
            )

        if classifications:
            self._repository.save_bulk(classifications)
