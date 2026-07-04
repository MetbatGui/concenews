"""News 모듈 domain 모델."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NewsItem(BaseModel):
    """뉴스 기사 도메인 모델.

    ID 는 IdGenerator (infrastructure) 가 발급, 생성 시 필수.
    Domain 은 생성 시점부터 identity 소유 (DDD).
    Frozen: 생성 후 필드 변경 불가 (aggregate 불변성).
    상세: docs/decisions/2026-07-04-id-strategy.md

    Attributes:
        id: 고유 식별자 (bigint sequence, 생성 시 필수).
        title: 뉴스 제목 (빈 문자열 거부).
        description: 요약 (외부 API 응답 누락 가능).
        link: 기사 원본 URL (dedup key).
        source: 출처 (신문사명).
        published_at: 발행 시간 (ISO8601 파싱).
        keywords: 쉼표 구분 키워드 (외부 API 응답 누락 가능).
        categories: 카테고리 리스트 (외부 API 응답 누락 가능).
    """

    model_config = ConfigDict(frozen=True)

    id: int
    title: str = Field(..., min_length=1)
    description: str | None = Field(default=None)
    link: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1)
    published_at: datetime
    keywords: str = Field(default="")
    categories: list[str] = Field(default_factory=list)
