"""Application service — 마켓 분류 오케스트레이션.

Walking Skeleton: 최소 흐름 (fetch → classify → save).
실제 흐름 (에러 처리, 부분 성공 등) 정교화는 후속 PR 에서.
"""

from datetime import UTC, datetime
import logging

import httpx

from src.modules.market.application.ports import (
    ClassificationRepositoryPort,
    MarketSourcePort,
    ParticipantSnapshotRepositoryPort,
    ParticipantSourcePort,
    SnapshotIdGeneratorPort,
    SnapshotRepositoryPort,
)
from src.modules.market.domain.classifier import classify
from src.modules.market.domain.models import (
    MarketClassification,
    MarketParticipantSnapshot,
)


logger = logging.getLogger(__name__)


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
            limit=200, order="volume24hr", ascending=False
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


class MarketSnapshotService:
    """거래량 상위 거시경제 마켓의 스냅샷 수집 유스케이스."""

    def __init__(
        self,
        source: MarketSourcePort,
        classification_repository: ClassificationRepositoryPort,
        snapshot_repository: SnapshotRepositoryPort,
        id_generator: SnapshotIdGeneratorPort,
    ) -> None:
        """외부 소스, 분류 캐시, 저장소와 식별자 발급기를 조립한다."""
        self._source = source
        self._classification_repository = classification_repository
        self._snapshot_repository = snapshot_repository
        self._id_generator = id_generator

    async def run(self) -> None:
        """상위 200 후보 중 유효한 MACRO 상위 50개를 저장한다."""
        now = datetime.now(UTC)
        macro_ids = self._classification_repository.find_active_macro_condition_ids(now)
        if not macro_ids:
            return

        candidates = await self._source.fetch_active_market_snapshots(
            limit=200, order="volume24hr", ascending=False
        )
        selected = [
            candidate for candidate in candidates if candidate.market_id in macro_ids
        ][:50]
        snapshots = [
            candidate.to_snapshot(self._id_generator.generate(), now)
            for candidate in selected
        ]
        self._snapshot_repository.save_bulk(snapshots)


class MarketParticipantSnapshotService:
    """거래량 상위 마켓의 공개 상위 보유 포지션 수집 서비스."""

    def __init__(
        self,
        source: ParticipantSourcePort,
        market_snapshot_repository: SnapshotRepositoryPort,
        participant_snapshot_repository: ParticipantSnapshotRepositoryPort,
        id_generator: SnapshotIdGeneratorPort,
    ) -> None:
        """참여자 소스와 저장소를 조립한다."""
        self._source = source
        self._market_snapshot_repository = market_snapshot_repository
        self._participant_snapshot_repository = participant_snapshot_repository
        self._id_generator = id_generator

    async def run(self) -> None:
        """최신 추적 대상의 결과별 상위 보유 포지션을 저장한다."""
        tracked_markets = self._market_snapshot_repository.find_latest_tracked_markets(
            limit=50
        )
        observed_at = datetime.now(UTC)

        for market in tracked_markets:
            try:
                positions = await self._source.fetch_top_holder_positions(
                    condition_id=market.condition_id, limit=20
                )
            except httpx.HTTPError:
                logger.exception(
                    "마켓 참여자 포지션 수집에 실패했습니다: %s", market.market_id
                )
                continue

            snapshots = [
                MarketParticipantSnapshot(
                    id=self._id_generator.generate(),
                    market_id=market.market_id,
                    condition_id=market.condition_id,
                    wallet_address=position.wallet_address,
                    outcome_index=position.outcome_index,
                    position_amount=position.position_amount,
                    timestamp=observed_at,
                )
                for position in positions
            ]
            self._participant_snapshot_repository.save_bulk(snapshots)
