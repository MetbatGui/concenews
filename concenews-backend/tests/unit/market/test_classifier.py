"""Unit test — classify() blacklist → whitelist 로직."""
from src.modules.market.domain.classifier import (
    MACRO_IDS,
    NON_MACRO_IDS,
    classify,
)
from src.modules.market.domain.models import Classification


class TestClassify:
    """classify() 분류 로직."""

    def test_blacklist_hit_returns_non_macro(self):
        """Given: 태그 ID 집합이 NON_MACRO_IDS 와 교집합 있음
        When: classify()
        Then: NON_MACRO 반환.
        """
        sports_id = 1  # 'Sports'
        result = classify({sports_id})
        assert result is Classification.NON_MACRO

    def test_whitelist_hit_returns_macro(self):
        """Given: 태그 ID 집합이 MACRO_IDS 와 교집합 있음
        When: classify()
        Then: MACRO 반환.
        """
        fed_id = 159  # 'Fed'
        result = classify({fed_id})
        assert result is Classification.MACRO

    def test_blacklist_and_whitelist_hit_returns_non_macro(self):
        """Given: 블랙+화이트 동시 히트
        When: classify()
        Then: NON_MACRO 우선.
        """
        sports_id = 1
        fed_id = 159
        result = classify({sports_id, fed_id})
        assert result is Classification.NON_MACRO

    def test_no_hit_returns_none(self):
        """Given: 태그 ID 집합이 두 리스트 모두와 교집합 없음
        When: classify()
        Then: None (UNKNOWN) 반환.
        """
        unknown_id = 999_999
        result = classify({unknown_id})
        assert result is None

    def test_empty_tags_returns_none(self):
        """Given: 빈 태그 집합
        When: classify()
        Then: None 반환.
        """
        result = classify(set())
        assert result is None


class TestTagIdSets:
    """TAG_IDS 상수 sanity check (spike LEARNINGS 매핑 확인)."""

    def test_macro_ids_contain_expected_tags(self):
        """LEARNINGS 확정 MACRO 태그 몇 개 존재 검증."""
        assert 120 in MACRO_IDS      # Finance
        assert 159 in MACRO_IDS      # Fed
        assert 235 in MACRO_IDS      # Bitcoin
        assert 100265 in MACRO_IDS   # Geopolitics
        assert 2 in MACRO_IDS        # Politics (넓게 포함)

    def test_non_macro_ids_contain_expected_tags(self):
        """LEARNINGS 확정 NON_MACRO 태그 몇 개 존재 검증."""
        assert 1 in NON_MACRO_IDS        # Sports
        assert 100350 in NON_MACRO_IDS   # Soccer
        assert 53 in NON_MACRO_IDS       # Movies
        assert 596 in NON_MACRO_IDS      # Culture
        assert 756 in NON_MACRO_IDS      # Epstein

    def test_no_overlap_between_lists(self):
        """블랙/화이트 상호 배타."""
        assert MACRO_IDS.isdisjoint(NON_MACRO_IDS)
