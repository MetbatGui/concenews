"""Cache adapter unit tests.

GWT (Given-When-Then) 형식.
"""
from freezegun import freeze_time
from src.modules.news.infrastructure.cache import InMemoryCacheAdapter


def test_cache_set_and_contains():
    """Given: empty cache
    When: set(key, ttl) called
    Then: contains(key) returns True
    """
    cache = InMemoryCacheAdapter()
    cache.set("link1", ttl_seconds=10)
    assert cache.contains("link1") is True


def test_cache_contains_missing_key():
    """Given: empty cache
    When: contains(missing_key) called
    Then: returns False
    """
    cache = InMemoryCacheAdapter()
    assert cache.contains("missing") is False


def test_cache_ttl_expiry():
    """Given: cache with short TTL
    When: TTL elapses
    Then: contains() returns False
    """
    with freeze_time("2026-07-06 12:00:00") as frozen_time:
        cache = InMemoryCacheAdapter()
        cache.set("link1", ttl_seconds=10)
        assert cache.contains("link1") is True

        frozen_time.move_to("2026-07-06 12:00:11")
        assert cache.contains("link1") is False


def test_cache_multiple_keys():
    """Given: cache with multiple keys
    When: querying different keys
    Then: each returns correct state
    """
    cache = InMemoryCacheAdapter()
    cache.set("link1", ttl_seconds=10)
    cache.set("link2", ttl_seconds=10)

    assert cache.contains("link1") is True
    assert cache.contains("link2") is True
    assert cache.contains("link3") is False


def test_cache_overwrite():
    """Given: cache with existing key
    When: set() called again with same key
    Then: TTL resets
    """
    with freeze_time("2026-07-06 12:00:00") as frozen_time:
        cache = InMemoryCacheAdapter()
        cache.set("link1", ttl_seconds=5)
        frozen_time.move_to("2026-07-06 12:00:04")

        cache.set("link1", ttl_seconds=10)
        frozen_time.move_to("2026-07-06 12:00:13")
        assert cache.contains("link1") is True  # TTL reset
