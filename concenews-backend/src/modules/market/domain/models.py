"""Market 도메인 모델.

Walking Skeleton 단계: 최소 필드만 정의. 후속 PR 에서 필드/불변식 확장.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, model_validator


class Classification(str, Enum):
    """마켓 분류 결과."""

    MACRO = "MACRO"
    NON_MACRO = "NON_MACRO"


class Tag(BaseModel):
    """Polymarket 태그.

    Attributes:
        id: Gamma API 태그 ID.
        label: 태그 표시명.
        slug: 태그 slug.
    """

    model_config = ConfigDict(frozen=True)

    id: int
    label: str
    slug: str


class MarketMetadata(BaseModel):
    """Gamma API 마켓 메타데이터.

    Attributes:
        condition_id: Polymarket condition ID (식별자).
        question: 마켓 질문.
        end_date: 마켓 종료일 (UTC).
    """

    model_config = ConfigDict(frozen=True)

    condition_id: str
    question: str
    end_date: datetime


class MarketClassification(BaseModel):
    """분류 결과 (도메인 aggregate).

    Attributes:
        condition_id: Polymarket condition ID.
        question: 마켓 질문.
        classification: MACRO 또는 NON_MACRO.
        tags: 분류에 사용된 태그 튜플.
        end_date: 캐시 만료 기준.
        classified_at: 분류 시각.
    """

    model_config = ConfigDict(frozen=True)

    condition_id: str
    question: str
    classification: Classification
    tags: tuple[Tag, ...]
    end_date: datetime
    classified_at: datetime


class MarketSnapshot(BaseModel):
    """거래량 상위 마켓의 한 시점 관측값.

    동일 마켓이라도 수집 시각이 다르면 각각 별도 관측값이다. 결과 이름과
    결과별 확률은 외부 API의 순서를 보존하는 immutable tuple로 둔다.

    Attributes:
        id: 스냅샷 고유 식별자(UUID v7).
        market_id: Gamma API 시장 식별자.
        question: 시장 질문.
        outcomes: 결과 이름의 순서 있는 목록.
        outcome_prices: outcomes와 같은 순서의 결과별 확률.
        last_price: 가장 최근 체결 가격.
        best_bid: 최고 매수 호가.
        best_ask: 최저 매도 호가.
        spread: 호가 스프레드.
        liquidity: 시장 유동성.
        volume_24h: 최근 24시간 거래량.
        volume_1w: 최근 1주 거래량.
        volume_1m: 최근 1개월 거래량.
        end_date: 시장 종료 시각(UTC).
        active: 활성 상태.
        closed: 종료 상태.
        timestamp: 스냅샷 수집 시각(UTC).
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    market_id: str = Field(min_length=1)
    condition_id: str | None = Field(default=None, min_length=1)
    question: str = Field(min_length=1)
    outcomes: tuple[str, ...]
    outcome_prices: tuple[float, ...]
    last_price: float | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    spread: float | None = None
    liquidity: float | None = None
    volume_24h: float | None = None
    volume_1w: float | None = None
    volume_1m: float | None = None
    end_date: AwareDatetime
    active: bool
    closed: bool
    timestamp: AwareDatetime

    @model_validator(mode="after")
    def _validate_outcome_price_pairs(self) -> "MarketSnapshot":
        """결과 이름·확률의 유효한 일대일 대응을 검증한다."""
        if not self.outcomes:
            raise ValueError("결과가 하나 이상 있어야 합니다.")
        if len(self.outcomes) != len(self.outcome_prices):
            raise ValueError("결과 이름과 확률의 개수가 일치해야 합니다.")
        if any(not 0.0 <= price <= 1.0 for price in self.outcome_prices):
            raise ValueError("결과별 확률은 0과 1 사이여야 합니다.")
        return self


class MarketSnapshotPayload(BaseModel):
    """외부 소스가 제공한 스냅샷 원본을 Domain 스냅샷으로 변환하는 값 객체."""

    model_config = ConfigDict(frozen=True)

    market_id: str = Field(min_length=1)
    condition_id: str | None = Field(default=None, min_length=1)
    question: str = Field(min_length=1)
    outcomes: tuple[str, ...]
    outcome_prices: tuple[float, ...]
    last_price: float | None = None
    best_bid: float | None = None
    best_ask: float | None = None
    spread: float | None = None
    liquidity: float | None = None
    volume_24h: float | None = None
    volume_1w: float | None = None
    volume_1m: float | None = None
    end_date: AwareDatetime
    active: bool
    closed: bool

    @model_validator(mode="after")
    def _validate_outcome_price_pairs(self) -> "MarketSnapshotPayload":
        """결과별 확률이 유효한 일대일 대응인지 검증한다."""
        if not self.outcomes:
            raise ValueError("결과가 하나 이상 있어야 합니다.")
        if len(self.outcomes) != len(self.outcome_prices):
            raise ValueError("결과 이름과 확률의 개수가 일치해야 합니다.")
        if any(not 0.0 <= price <= 1.0 for price in self.outcome_prices):
            raise ValueError("결과별 확률은 0과 1 사이여야 합니다.")
        return self

    def to_snapshot(self, snapshot_id: UUID, timestamp: datetime) -> MarketSnapshot:
        """수집 시각과 식별자를 부여한 불변 스냅샷을 만든다."""
        return MarketSnapshot(
            id=snapshot_id,
            market_id=self.market_id,
            condition_id=self.condition_id,
            question=self.question,
            outcomes=self.outcomes,
            outcome_prices=self.outcome_prices,
            last_price=self.last_price,
            best_bid=self.best_bid,
            best_ask=self.best_ask,
            spread=self.spread,
            liquidity=self.liquidity,
            volume_24h=self.volume_24h,
            volume_1w=self.volume_1w,
            volume_1m=self.volume_1m,
            end_date=self.end_date,
            active=self.active,
            closed=self.closed,
            timestamp=timestamp,
        )


class TrackedMarket(BaseModel):
    """참여자 보유 포지션 수집 대상 마켓의 외부 식별자 쌍."""

    model_config = ConfigDict(frozen=True)

    market_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)


class MarketParticipantSnapshot(BaseModel):
    """한 지갑의 결과별 공개 보유 포지션 관측값."""

    model_config = ConfigDict(frozen=True)

    id: UUID
    market_id: str = Field(min_length=1)
    condition_id: str = Field(min_length=1)
    wallet_address: str = Field(min_length=1)
    outcome_index: int = Field(ge=0)
    position_amount: float = Field(gt=0)
    timestamp: AwareDatetime
