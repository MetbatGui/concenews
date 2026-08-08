"""TheNewsAPI top-news 응답 계약 fixture.

Spike에서 확인한 `data` 최상위 키와 기사 필드 형식을 보존한다.
외부 응답 계약이 바뀌면 이 파일을 먼저 갱신한다.
"""
from copy import deepcopy
from typing import Any


ARTICLE_ONE = {
    "title": "Interest Rate Decision",
    "description": "Central bank raises rates",
    "url": "https://example.com/news/1",
    "source": "Financial News",
    "published_at": "2026-07-06T03:00:00Z",
}

ARTICLE_TWO = {
    "title": "Currency Market Update",
    "description": None,
    "url": "https://example.com/news/2",
    "source": "Market Daily",
    "published_at": "2026-07-06T04:00:00Z",
}


def top_news_response(*articles: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """TheNewsAPI top-news 응답 형식으로 기사를 감싼다.

    Args:
        *articles: TheNewsAPI 기사 형식의 데이터.

    Returns:
        `data` 키를 갖는 독립된 응답 dict.
    """
    return {"data": deepcopy(list(articles))}
