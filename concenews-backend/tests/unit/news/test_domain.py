"""NewsItem domain 모델 unit tests."""
from datetime import datetime

import pytest
from pydantic import ValidationError

from src.modules.news.domain.models import NewsItem


class TestNewsItem:
    """NewsItem domain 모델 검증."""

    def test_news_item_creates_with_valid_fields(self):
        """유효한 필드로 NewsItem 이 생성된다.

        Given: id 포함 모든 필수 필드
        When: NewsItem 생성
        Then: 인스턴스 반환, published_at 은 datetime
        """
        item = NewsItem(
            id=1,
            title="Fed 금리 인상",
            link="https://example.com/1",
            source="Reuters",
            published_at="2026-07-03T10:30:00Z",
        )
        assert item.id == 1
        assert item.title == "Fed 금리 인상"
        assert isinstance(item.published_at, datetime)

    def test_news_item_requires_id(self):
        """id 없이 생성 시 ValidationError.

        Given: id 필드 생략
        When: NewsItem 생성
        Then: ValidationError (Domain 은 생성 시 identity 필수)
        """
        with pytest.raises(ValidationError):
            NewsItem(
                title="t",
                link="https://x",
                source="x",
                published_at="2026-07-03T10:30:00Z",
            )

    @pytest.mark.parametrize("field", ["title", "link", "source"])
    def test_news_item_rejects_empty_required_field(self, field):
        """필수 str 필드는 빈 문자열을 거부한다.

        Given: 하나의 필수 str 필드가 빈 문자열
        When: NewsItem 생성
        Then: ValidationError
        """
        base = dict(
            id=1,
            title="t",
            link="https://x",
            source="x",
            published_at="2026-07-03T10:30:00Z",
        )
        base[field] = ""
        with pytest.raises(ValidationError):
            NewsItem(**base)

    def test_news_item_allows_missing_description(self):
        """description 없어도 생성 가능 (외부 API 응답 누락 대응).

        Given: description 필드 생략
        When: NewsItem 생성
        Then: description 은 None
        """
        item = NewsItem(
            id=1,
            title="t",
            link="https://x",
            source="x",
            published_at="2026-07-03T10:30:00Z",
        )
        assert item.description is None

    def test_news_item_parses_iso8601_published_at(self):
        """published_at 은 ISO8601 문자열을 datetime 으로 변환한다.

        Given: "2026-07-03T10:30:00Z" 형식
        When: NewsItem 생성
        Then: published_at 은 datetime 인스턴스
        """
        item = NewsItem(
            id=1,
            title="t",
            link="https://x",
            source="x",
            published_at="2026-07-03T10:30:00Z",
        )
        assert isinstance(item.published_at, datetime)

    def test_news_item_rejects_invalid_published_at(self):
        """잘못된 형식의 published_at 은 거부한다.

        Given: published_at 이 non-ISO8601 문자열
        When: NewsItem 생성
        Then: ValidationError
        """
        with pytest.raises(ValidationError):
            NewsItem(
                id=1,
                title="t",
                link="https://x",
                source="x",
                published_at="어제",
            )
