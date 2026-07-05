# ADR: Test 격리 패턴 — `lru_cache.cache_clear()` (InMemory 스코프)

**Status**: Accepted
**Date**: 2026-07-05
**Slice**: news-fetch

---

## Context

Wire-up 완료 시점, Repository 를 `@lru_cache(maxsize=1)` module-level 싱글톤으로 관리 중.
Test 는 `app.dependency_overrides[get_repository] = lambda: fresh_repo` 로 우회하여 격리하고 있으나, 미래 실수 방지 위해 명시적 teardown 필요.

## Options Considered

| 옵션 | 격리 방식 | InMemory | PG (미래) | 복잡도 |
|------|----------|----------|-----------|--------|
| A. Instance-per-test (현재) | Fixture 새 인스턴스 + DI override | ✅ | ❌ Connection pool 재생성 못함 | 낮음 |
| **B. `cache_clear()` teardown** | Singleton 인스턴스 자동 교체 | ✅ | — (transaction 로 별도 대응) | 최저 |
| C. `Repository.clear()` interface | State 리셋 메서드 | ✅ | 이용 안 함 (transaction rollback) | 중간 (test-driven 인터페이스) |
| D. `app.state` + lifespan | 인스턴스 유지, `app.state` 재세팅 | ✅ | ✅ | 재구성 필요 |

## Decision

**B: `cache_clear()` teardown**.

`tests/conftest.py` 에 autouse fixture 추가하여 매 test 후 `get_repository.cache_clear()` 자동 호출.

```python
# tests/conftest.py
import pytest
from src.modules.news.bootstrap import get_repository


@pytest.fixture(autouse=True)
def _clear_singleton_cache():
    """매 test 후 module-level lru_cache 자동 clear (격리)."""
    yield
    get_repository.cache_clear()
```

## Rationale

- **얇음**: 5 라인. Boilerplate 최소.
- **명시적 격리**: 지금은 dependency_overrides 로 우회하므로 실제 stale 안 됨. Teardown 은 "미래 실수 방지" 목적.
- **Repository 인터페이스 유지**: `clear()` 추가 = test-driven API smell. Production 은 `clear()` 안 씀.
- **PG 로 갈 때 별도 패턴 자연**: PG test 는 **transaction rollback** 관용. `Repository.clear()` 통일한다고 이득 없음 — 어차피 fixture 재작성.
- **YAGNI**: Speculative interface 확장 회피.

## Reconsider When

- Test 격리가 실제로 깨지는 케이스 발생 (예: `pytest-xdist` 병렬 실행 시 module-level state 공유 문제)
- Repository 가 다른 리소스 (event bus, cache) 와 함께 관리 필요 → `app.state` (옵션 D) 로 통합 재검토
- Concurrent async test → module-level singleton 이 race 위험 → 재검토

## Migration Path (미래 PG 도입 시)

PG Repository = SQLAlchemy session 기반. Test 격리 방식 전환:

```python
# 미래 tests/conftest.py (PG 도입 후)
@pytest.fixture(autouse=True)
def _db_session():
    conn = engine.connect()
    trans = conn.begin()
    session = SessionLocal(bind=conn)
    # dependency_overrides[get_session] = lambda: session
    yield session
    trans.rollback()  # ← 이것이 새 격리 방식
    conn.close()
```

`cache_clear()` fixture 는 제거, transaction rollback fixture 로 대체.
Repository 인터페이스 자체는 변경 없음 (save/find_all 만).

**핵심**: InMemory 와 PG 는 다른 격리 메커니즘 사용. 통일 시도 자체가 premature.

## References

- [ADR 2026-07-05 id-strategy-uuidv7](./2026-07-05-id-strategy-uuidv7.md)
- Test 컨벤션: [testing.md](../../concenews-backend/docs/conventions/testing.md)
