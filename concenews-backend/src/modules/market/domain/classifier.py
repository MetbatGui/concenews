"""마켓 분류 함수 (Walking Skeleton 스텁).

실제 TAG_IDS 및 분류 로직은 PR #2에서 확장.
"""
from src.modules.market.domain.models import Classification


NON_MACRO_IDS: frozenset[int] = frozenset()
MACRO_IDS: frozenset[int] = frozenset()


def classify(tag_ids: set[int]) -> Classification | None:
    """태그 ID 집합으로 분류.

    Walking Skeleton: 항상 MACRO 반환 (스텁).
    PR #2에서 blacklist → whitelist 로직 실제 구현.

    Args:
        tag_ids: 마켓의 태그 ID 집합.

    Returns:
        Classification.MACRO (스텁).
    """
    del tag_ids
    return Classification.MACRO
