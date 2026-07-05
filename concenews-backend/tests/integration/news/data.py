"""News integration test 용 fixture data (Object Mother 패턴).

Hardcoded NewsItem 상수. 결정성 + assertion 강도 확보.
상세: docs/decisions/2026-07-05-test-fixture-data-pattern.md
Timezone: KST 저장 (docs/decisions/2026-07-05-timezone-policy.md)
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from src.modules.news.domain.models import NewsItem

KST = timezone(timedelta(hours=9))

NEWS_OLD = NewsItem(
    id=UUID("01912345-6789-7abc-8def-000000000001"),
    title="오래된 뉴스",
    link="https://example.com/old",
    source="Reuters",
    published_at=datetime(2020, 1, 1, tzinfo=KST),
)

NEWS_MID = NewsItem(
    id=UUID("01912345-6789-7abc-8def-000000000002"),
    title="중간 뉴스",
    link="https://example.com/mid",
    source="Reuters",
    published_at=datetime(2023, 1, 1, tzinfo=KST),
)

NEWS_NEW = NewsItem(
    id=UUID("01912345-6789-7abc-8def-000000000003"),
    title="최신 뉴스",
    link="https://example.com/new",
    source="Reuters",
    published_at=datetime(2026, 1, 1, tzinfo=KST),
)
