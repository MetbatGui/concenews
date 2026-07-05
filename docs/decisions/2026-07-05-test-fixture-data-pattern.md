# ADR: Integration Test Fixture Data 패턴 — Object Mother (Hardcoded Constants)

**Status**: Accepted
**Date**: 2026-07-05
**Slice**: news-fetch

---

## Context

Wire-up PR 진행 중 두 관련 이슈:

1. **Cross-conftest import** (`from tests.integration.conftest import _make_news`)
   - pytest 관용 위반 (conftest 는 fixture/hook 전용, helper 저장소 아님)
   - Package 구조 dependency (`tests/__init__.py` 필요)
2. **Weak assertion** (`assert item.title` — truthy 만 확인)
   - Domain → DTO 매핑 실수 catch 못 함
   - Factory 는 random UUID 생성 → 특정 값 참조 불가

Factory (`_make_news(title=..., published_at=...)`) 로 데이터 만들면:
- 매 test 마다 다른 UUID → test 간 결정성 없음
- Fixture assertion 은 `filled_repository.find_all()[0]` 처럼 우회 참조
- Cross-file 헬퍼 재사용은 conftest import 로 이어짐

## Options Considered

| 옵션 | Cross-conftest | 결정성 | Assertion 강도 | 다양성 |
|------|---------------|--------|---------------|--------|
| A. Factory + conftest (현재) | 있음 (issue) | 없음 | 약함 | 자유 |
| B. Factory → `tests/factories.py` regular module | 없음 | 없음 | 약함 | 자유 |
| **C. Hardcoded constants (Object Mother)** | 없음 | 있음 | **강함** (상수 직접 비교) | 제한 (필요시 상수 추가) |
| D. pytest fixture factory | 없음 | 없음 | 약함 | 자유 |

## Decision

**C: Hardcoded Constants (Object Mother 패턴)** — Integration test 만 적용.

- Module: `tests/integration/{module}/data.py`
- 상수: `NEWS_OLD`, `NEWS_MID`, `NEWS_NEW` 등 명명된 test data
- Fixture: 상수를 `InMemoryNewsRepository(initial=[...])` 로 주입

**Unit test 는 그대로**: 각 파일 안 `_make_item` 헬퍼 유지 (cross-conftest 아님, uniqueness 검증 필요한 경우 있음).

### 구조

```python
# tests/integration/news/data.py
NEWS_OLD = NewsItem(id=UUID("...-01"), title="오래된 뉴스", published_at=..., ...)
NEWS_MID = NewsItem(id=UUID("...-02"), title="중간 뉴스", published_at=..., ...)
NEWS_NEW = NewsItem(id=UUID("...-03"), title="최신 뉴스", published_at=..., ...)

# tests/integration/news/conftest.py
from tests.integration.news.data import NEWS_OLD, NEWS_MID, NEWS_NEW

@pytest.fixture
def filled_repository():
    return InMemoryNewsRepository(initial=[NEWS_OLD, NEWS_MID, NEWS_NEW])

# tests/integration/news/test_news_acceptance.py
def test_sorted(self, filled_client):
    data = ...
    assert [item.id for item in data.news] == [NEWS_NEW.id, NEWS_MID.id, NEWS_OLD.id]
```

## Rationale

- **결정성**: UUID 고정 → test 결과 재현 가능
- **Assertion 강도**: `NEWS_NEW.id` 직접 참조 → Domain → DTO 매핑 실수 catch
- **Pytest 관용 준수**: Regular module import, cross-conftest 없음
- **가독성**: `NEWS_NEW` = "무엇이 저장된 것인가" 명확
- **Frozen NewsItem 안전**: Immutable → module constant 로 공유해도 test 간 오염 없음
- **Object Mother 패턴** (Martin Fowler): 잘 알려진 test 패턴, 팀 확장 시 학습 곡선 낮음

## Reconsider When

- Test data variance 요구 급증 (수십 개 case) → factory + parametrize 하이브리드 재검토
- Domain schema 자주 변경 → 상수 갱신 부담 → factory 로 회귀
- Test 가 상태 변경 시나리오 (mutation) 를 다뤄야 함 → Domain mutable 로 갔을 때 재검토

## Migration Path (미래 PG 도입 시)

Constants 자체는 backend-agnostic (`NewsItem` 은 순수 Pydantic 모델).
- InMemory: `initial=[NEWS_OLD, ...]` (지금 방식)
- PG: 매 test setup 에서 `session.add_all([NEWS_OLD, ...])` (동일 상수 재사용)

**핵심**: Object Mother 는 backend 무관. Test 격리 방식 ([ADR test-isolation-cache-clear](./2026-07-05-test-isolation-cache-clear.md)) 이 backend 별로 다를 뿐.

## References

- Martin Fowler — "Object Mother" pattern
- [ADR 2026-07-05 test-isolation-cache-clear](./2026-07-05-test-isolation-cache-clear.md)
- Test 컨벤션: [testing.md](../../concenews-backend/docs/conventions/testing.md)
- pytest 공식: conftest 는 fixture/hook 전용
