"""응답 모델 (DTO) - News 모듈의 API 계약."""
from pydantic import BaseModel, ConfigDict, Field


class NewsItemResponse(BaseModel):
    """뉴스 기사 응답 모델.

    Given: API 응답 계약
    When: 클라이언트가 /news 호출
    Then: 이 구조의 JSON 반환
    """

    id: str = Field(..., description="고유 식별자 (URL 해시)")
    title: str = Field(..., description="뉴스 제목")
    description: str = Field(..., description="요약 설명")
    link: str = Field(..., description="기사 원본 링크")
    source: str = Field(..., description="뉴스 출처 (신문사명)")
    published_at: str = Field(..., description="발행 시간 (ISO8601)")
    keywords: str = Field(default="", description="검색 키워드 (쉼표 구분)")
    categories: list[str] = Field(default_factory=list, description="카테고리 (자동 추출)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "abc123def456",
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

    news: list[NewsItemResponse] = Field(
        default_factory=list, description="뉴스 기사 목록"
    )
    count: int = Field(default=0, description="반환된 기사 개수")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "news": [
                    {
                        "id": "abc123def456",
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
