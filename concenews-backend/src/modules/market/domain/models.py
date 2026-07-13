"""Market 도메인 모델.

Walking Skeleton 단계: 최소 필드만 정의. 후속 PR 에서 필드/불변식 확장.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


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
