"""Cache adapter (infrastructure).

In-memory cache with TTL support.
"""
import time


class InMemoryCacheAdapter:
    """메모리 기반 TTL 캐시.

    특징:
    - Key-value 저장 (dict 기반)
    - TTL 만료 시 자동 정리
    - Thread-safe 아님 (단일 스레드 ASGI 환경 가정)

    상세: ponytail (dict + timestamp, stdlib only)
    """

    def __init__(self) -> None:
        """Initialize empty cache.

        _cache: {key: expiry_timestamp}
        """
        self._cache: dict[str, float] = {}

    def set(self, key: str, ttl_seconds: int) -> None:
        """Set cache entry with TTL.

        Args:
            key: Cache key.
            ttl_seconds: Time-to-live in seconds.
        """
        expiry = time.time() + ttl_seconds
        self._cache[key] = expiry

    def contains(self, key: str) -> bool:
        """Check if cache entry exists and is not expired.

        Expired entries are removed on check.

        Args:
            key: Cache key.

        Returns:
            True if key exists and is valid.
        """
        if key not in self._cache:
            return False

        if time.time() > self._cache[key]:
            del self._cache[key]
            return False

        return True
