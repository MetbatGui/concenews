"""PostgreSQL 뉴스 저장소 (PgNewsRepository).

Domain (NewsItem, Pydantic frozen) ↔ ORM (NewsRow, SQLAlchemy) 변환은 이 파일의
_to_domain / _to_orm 함수가 담당. 두 세계 명확히 분리 (혼용 금지).

상세: docs/decisions/2026-07-06-repository-strategy.md
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.news.domain.models import NewsItem
from src.modules.news.infrastructure.repositories.orm import NewsRow


def _to_domain(row: NewsRow) -> NewsItem:
    """ORM → Domain 변환."""
    return NewsItem(
        id=row.id,
        title=row.title,
        description=row.description,
        link=row.link,
        source=row.source,
        published_at=row.published_at,
        keywords=row.keywords,
        categories=tuple(row.categories),
    )


def _to_orm(item: NewsItem) -> NewsRow:
    """Domain → ORM 변환."""
    return NewsRow(
        id=item.id,
        title=item.title,
        description=item.description,
        link=item.link,
        source=item.source,
        published_at=item.published_at,
        keywords=item.keywords,
        categories=list(item.categories),
    )


class PgNewsRepository:
    """PostgreSQL 저장소.

    NewsRepositoryPort 구현체.
    Session 은 생성자 주입 (transaction 스코프 = 호출자 책임).

    Attributes:
        _session: SQLAlchemy Session (request-scoped 권장).
    """

    def __init__(self, session: Session):
        self._session = session

    def save(self, item: NewsItem) -> None:
        """뉴스 upsert. 같은 id 존재 시 update.

        Args:
            item: 저장할 NewsItem.
        """
        self._session.merge(_to_orm(item))
        self._session.flush()

    def find_all(self) -> list[NewsItem]:
        """저장된 모든 뉴스 반환.

        Returns:
            NewsItem 리스트 (순서 미보장).
        """
        rows = self._session.execute(select(NewsRow)).scalars().all()
        return [_to_domain(row) for row in rows]
