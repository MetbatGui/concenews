"""요청/응답 모델 (DTO) - News 모듈의 API 계약."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GetNewsRequest(BaseModel):
    """GET /news 요청 파라미터 모델.

    Attributes:
        limit: 반환할 최대 기사 수. 기본 50, 최소 1, 최대 100.
            Endpoint boundary validation (Service 는 valid 가정).
    """

    limit: int = Field(default=50, ge=1, le=100, description="최대 반환 개수")


class NewsItemResponse(BaseModel):
    """뉴스 기사 응답 모델.

    Given: API 응답 계약
    When: 클라이언트가 /news 호출
    Then: 이 구조의 JSON 반환
    """

    id: UUID = Field(..., description="고유 식별자 (UUID v7)")
    title: str = Field(..., description="뉴스 제목")
    description: str | None = Field(default=None, description="요약 설명 (API 응답에서 누락될 수 있음)")
    link: str = Field(..., description="기사 원본 링크")
    source: str = Field(..., description="뉴스 출처 (신문사명)")
    published_at: datetime = Field(..., description="발행 시간 (ISO8601)")
    keywords: str = Field(default="", description="검색 키워드 (쉼표 구분)")
    categories: list[str] = Field(default_factory=list, description="카테고리 (자동 추출)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "01912345-6789-7abc-8def-0123456789ab",
                "title": "연방준비제도, 기준금리 인상",
                "description": "미국 연방준비제도가 기준금리를 25bp 인상했습니다.",
                "link": "https://example.com/news/123",
                "source": "Reuters",
                "published_at": "2026-07-03T10:30:00Z",
                "keywords": "fed,interest rate,usd",
                "categories": ["finance", "monetary-policy"],
            }
        }
    )


class GetNewsResponse(BaseModel):
    """GET /news 엔드포인트 응답 모델.

    Given: 클라이언트 요청
    When: GET /news 호출
    Then: news 배열과 count 반환
    """

    news: list[NewsItemResponse] = Field(description="뉴스 기사 목록")
    count: int = Field(description="반환된 기사 개수")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "news": [
                    {
                        "id": "01912345-6789-7abc-8def-0123456789ab",
                        "title": "연방준비제도, 기준금리 인상",
                        "description": "미국 연방준비제도가 기준금리를 25bp 인상했습니다.",
                        "link": "https://example.com/news/123",
                        "source": "Reuters",
                        "published_at": "2026-07-03T10:30:00Z",
                        "keywords": "fed,interest rate,usd",
                        "categories": ["finance", "monetary-policy"],
                    }
                ],
                "count": 1,
            }
        }
    )
