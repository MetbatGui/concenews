"""NewsItem domain 모델 unit tests."""
from datetime import datetime

import pytest
from pydantic import ValidationError
from uuid_utils.compat import uuid7

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
            id=uuid7(),
            title="Fed 금리 인상",
            link="https://example.com/1",
            source="Reuters",
            published_at="2026-07-03T10:30:00Z",
        )
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
            id=uuid7(),
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
            id=uuid7(),
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
            id=uuid7(),
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
                id=uuid7(),
                title="t",
                link="https://x",
                source="x",
                published_at="어제",
            )

    def test_news_item_rejects_naive_datetime(self):
        """naive datetime 은 거부한다 (AwareDatetime 강제).

        Given: tzinfo 없는 naive datetime
        When: NewsItem 생성
        Then: ValidationError

        Timezone 정책: docs/decisions/2026-07-05-timezone-policy.md
        """
        with pytest.raises(ValidationError):
            NewsItem(
                id=uuid7(),
                title="t",
                link="https://x",
                source="x",
                published_at=datetime(2020, 1, 1),  # naive
            )

    def test_news_item_is_immutable(self):
        """생성 후 필드 변경 시도는 거부된다 (frozen).

        Given: 생성된 NewsItem 인스턴스
        When: 필드 mutation 시도 (item.title = "새 제목")
        Then: ValidationError

        Domain identity/state 는 생성 시점 고정. Aggregate 불변성 강제.
        Repository 저장 값이 호출자에 의해 오염될 위험 제거.
        """
        item = NewsItem(
            id=uuid7(),
            title="원본",
            link="https://x",
            source="x",
            published_at="2026-07-03T10:30:00Z",
        )
        with pytest.raises(ValidationError):
            item.title = "변경"

    def test_news_item_categories_stored_as_immutable_tuple(self):
        """categories 는 immutable tuple 로 저장된다.

        Given: categories 로 list 전달
        When: NewsItem 생성 후 categories 접근
        Then: tuple 타입, 값 순서 유지

        frozen=True 는 attribute 재할당만 막음. 컨테이너 mutation
        (list.append) 방지하려면 컨테이너 자체가 immutable 이어야 함.
        정책: docs/conventions/immutability.md
        """
        item = NewsItem(
            id=uuid7(),
            title="t",
            link="https://x",
            source="x",
            published_at="2026-07-03T10:30:00Z",
            categories=["general", "politics"],
        )
        assert isinstance(item.categories, tuple)
        assert item.categories == ("general", "politics")
