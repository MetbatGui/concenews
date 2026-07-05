# ADR: Repository 전략 — Port 추출, Test 전략, InMemory 역할

**Status**: Accepted
**Date**: 2026-07-06
**Slice**: news-collection (news 모듈)

---

## Context

news-fetch slice 에서 `InMemoryNewsRepository` 만 존재. Rule of Three 준수로 Protocol 미도입.

news-collection slice 에서 `PgNewsRepository` 도입 예정 → **2번째 impl 등장** = Port 추출 시점.
동시에 다음도 결정 필요:
- Test 전략 (Repository layer 단위 / 통합 test 어떻게?)
- `InMemoryNewsRepository` 역할 재정의 (production default → test fake?)

## Options Considered

### Port 추출 시점
| 옵션 | 이유 |
|------|------|
| **A. 지금 (PR #3)** | Rule of Three 트리거 매칭, 두 impl 자연스레 계약 정형화 |
| B. 다중 impl 후 | 최소 3개 될 때까지 대기 → 지연, PR #3 이 impl 없이 진행 못 함 |

### Test 전략
| 옵션 | Pros | Cons |
|------|------|------|
| **A. Fake (InMemory) + 실 PG integration** | 고전파 정합, state 검증, refactor safe | Docker 필요 |
| B. Mock session/engine | 격리 완벽 | Interaction chain 복잡, refactor 취약 |
| C. SQLite in-memory for Pg | 빠름 | PG-specific (TIMESTAMPTZ, UUID) 못 봄 |

### InMemory 역할
| 옵션 | 특징 |
|------|------|
| **A. Test Fake (강등)** | Production 은 Pg. Service unit test 에서 Fake 로 사용. |
| B. Production 옵션 유지 | Env 별 (test / dev / prod) 선택 가능. 복잡. |

## Decision

**A + A + A** — Port 추출 지금, Fake+실PG test, InMemory 는 Fake 로 강등.

### 1. Port 추출
- `application/ports.py` 에 `NewsRepositoryPort` 추가:
  ```python
  class NewsRepositoryPort(Protocol):
      def save(self, item: NewsItem) -> None: ...
      def find_all(self, limit: int | None = None) -> list[NewsItem]: ...
  ```
- Adapters:
  - `infrastructure/repositories/in_memory.py` — `InMemoryNewsRepository` (기존 이관)
  - `infrastructure/repositories/postgres.py` — `PgNewsRepository` (신규)

### 2. Test 전략 (고전파 정합)
- **Domain unit test**: 그대로 (Pydantic 값 검증)
- **Service unit test**: `InMemoryNewsRepository` = Fake 로 주입
- **Repository unit test**: **skip** (SQLAlchemy 자체 test 안 함)
- **Repository integration test**: **실 PG** (docker-compose 활용)
  - Test 격리: transaction rollback fixture (autouse)
  - 파일 위치: `tests/integration/news/test_news_repository_postgres.py`
- **Acceptance test**: 기존대로 (`test_news_acceptance.py`)

### 3. InMemoryNewsRepository 역할
- Production 에서 사용 안 함 (bootstrap 은 Pg 주입)
- **Test Fake 용도로 유지** — Service unit test 편의
- 파일: `infrastructure/repositories/in_memory.py` 로 이동, 삭제 안 함

### 4. dependency_overrides 확장
- 기존 `get_repository` 는 그대로 유지
- Test 는 `InMemoryNewsRepository` fake 로 override
- Production 은 `PgNewsRepository` 주입

## Rationale

- **Rule of Three 준수**: 2번째 impl 도입 = Protocol 추출 자연 시점 (premature 아님)
- **고전파 정합**: 이미 프로젝트 관례 (mock 사용 0회, Fake 사용). Repository 도 같은 스타일.
- **테스트 격리 & 실 검증 균형**: Service test 는 빠른 Fake, Repository 는 실 PG 로 실 SQL 확인.
- **Refactor safe**: state-based test 는 내부 구조 변경에 강함.
- **InMemory 재활용**: 새 Fake 만들 필요 없음 (기존 impl 가 이미 Fake 역할 수행 가능).

## Reconsider When

- **모듈 확장**: market/matching 모듈이 Repository 필요 시 shared_kernel 로 Port 이관 재검토
- **테스트 성능 문제**: 실 PG integration test 가 느려짐 → testcontainers 도입 or SQLite fallback
- **Port 계약 변경**: `find_by_link`, `count` 등 새 메서드 필요 시 Port 확장
- **Async 전환** (MSA): Port 를 async 시그니처로 재작성 → 모든 adapter 재구현

## Migration Path (다음 slice)

### PR #3 (PgNewsRepository) 진행 순서
1. `application/ports.py` 에 `NewsRepositoryPort` Protocol 추가
2. `infrastructure/repositories/` 폴더 생성
3. 기존 `infrastructure/repositories.py` → `infrastructure/repositories/in_memory.py` 로 이동 (git mv)
4. `infrastructure/repositories/postgres.py` 신규 (`PgNewsRepository`)
5. `bootstrap.py`: Pg 주입 (환경 변수로 선택 가능 — 나중)
6. Integration test: `tests/integration/news/test_news_repository_postgres.py`
7. Alembic migration: `news` 테이블

## References

- [ADR 2026-07-06 db-library](./2026-07-06-db-library.md)
- [ADR 2026-07-05 timezone-policy](./2026-07-05-timezone-policy.md) — `TIMESTAMPTZ` 사용
- 고전파 (Kent Beck): state-based test, Fake 관용
- Test convention: [testing.md](../../concenews-backend/docs/conventions/testing.md)
