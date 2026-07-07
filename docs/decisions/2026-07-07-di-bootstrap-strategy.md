# ADR: Bootstrap DI & Lifespan 전략 — Production vs Test Repository 이원화

**Status**: Accepted
**Date**: 2026-07-07
**Slice**: news-collection-bootstrap (#22)

---

## Context

PR #22 에서 FastAPI lifespan + Scheduler 통합 시, **Production 과 Test 환경에서 Repository 구현체가 달라야 함**:

- **Production**: News collector 는 매 실행마다 새 Session 생성 (격리, lifecycle 단순화)
- **Test (Acceptance)**: `pg_session` fixture 로 transaction rollback (격리)
- **Test (Unit)**: `InMemoryNewsRepository` (빠름)

이를 **DI 계층에서 투명하게 처리**하면서, **테스트-프로덕션 간 신뢰도를 보증**해야 함.

## Problem

이전 상태:
- Acceptance test: `InMemoryNewsRepository` (mock)
- Production: `PgNewsRepository` (real)
- **결과**: 테스트 green 이 프로덕션 동작 보증하지 않음 ❌

### 근본 원인

**Repository 계약이 추상화(Port)되었지만, 테스트는 여전히 Fake(InMemory) 사용**
→ **"Fake 와 Real 의 동작 차이" 감지 불가**

### 예시

```python
# 테스트 (Fake)
repository = InMemoryNewsRepository()
collector.run()  # In-memory save → OK ✅

# 프로덕션 (Real PG)
repository = PgNewsRepository(session)
collector.run()  # SQL save 실패 (connection pool exhausted) → FAIL ❌
```

테스트 통과 ≠ 프로덕션 동작

## Options Considered

### 1. Test 계층 분리 전략

| 옵션 | 레벨 | Repository | 속도 | 실제 검증 |
|------|------|-----------|------|---------|
| **A. 3계층** | Unit (최소) | InMemory | 빠름 | ❌ |
| | Integration (부분) | InMemory | 빠름 | ❌ |
| | System (전체) | pg_session | 느림 | ✅ |
| B. 2계층 (mocks only) | Unit | InMemory | 빠름 | ❌ |
| | Integration | 모두 mock | 빠름 | ❌ |

### 2. DI 구현 패턴

| 옵션 | 방식 | Production | Test |
|------|------|-----------|------|
| **A. bootstrap 함수** | `get_repository(session)` 제공자 | PgNewsRepository(session) | override |
| B. 환경변수 | `REPO_TYPE=pg\|memory` | read at startup | override |
| C. Fixture 만 | conftest override 만 | hard-coded | fixture |

### 3. Per-Execution Session

| 옵션 | 방식 | 생성 | 정리 |
|------|------|------|------|
| **A. Scheduler closure** | `run_collector()` 내부 | `Session(get_engine())` | finally close |
| B. App-level session | `app.state.session` | startup | shutdown |
| C. Thread-local | `flask.g` 같은 pattern | 없음 (복잡) | 없음 |

## Decision

**A + A + A** — 3계층 test, bootstrap 함수, per-execution session.

### 1. Test 계층 설계

#### Unit Test (InMemoryNewsRepository)
```python
# tests/unit/news/test_news_collector_service.py
def test_collector_saves_to_repo(self):
    """Given: InMemoryNewsRepository + API mock
    When: collector.run()
    Then: 기사 저장 확인
    """
    api_mock = Mock(spec=NewsSourcePort)
    cache = InMemoryCacheAdapter()
    repository = InMemoryNewsRepository()
    
    collector = NewsCollectorService(api_mock, cache, repository)
    collector.run(keywords=[...])
    
    assert len(repository.find_all()) == 3  # Fake 동작 검증
```

**목적**: Service 로직 (dedup, error handling) 검증 (빠름, 격리됨)

#### Integration Test with Mock (E2E 신호)
```python
# tests/integration/news/test_news_collection_e2e.py
async def test_scheduler_runs_collector(self, pg_session):
    """Given: AsyncioScheduler + NewsCollectorService + API mock + Real DB
    When: scheduler.trigger()
    Then: API call → DB save 흐름 검증
    """
    with responses.RequestsMock() as rsps:
        # Mock API (구조는 Real API 와 동일)
        rsps.add(responses.GET, "https://api.thenewsapi.com/v1/news/top", 
                 json={"data": [...]}, status=200)
        
        repository = PgNewsRepository(pg_session)
        collector = NewsCollectorService(api_client, cache, repository)
        collector.run(keywords=[...])
        
        items = repository.find_all()
        assert len(items) == 3  # Real Repository 검증
```

**목적**: Scheduler + Service + Real Repository 협력 검증 (실제 DB 구조 확인)

#### System Acceptance Test (진정한 E2E)
```python
# tests/integration/news/test_news_system_acceptance.py
def test_get_news_returns_collected_data(self, pg_client_with_news_data):
    """Given: 3개 뉴스 ORM 적재 (Real API 응답 형태)
    When: GET /news
    Then: 적재된 뉴스 조회 + 정렬 확인
    """
    response = pg_client_with_news_data.get("/news")
    data = GetNewsResponse.model_validate(response.json())
    assert data.count == 3
    assert data.news[0].published_at >= data.news[1].published_at
```

**목적**: 전체 경로 (collection → DB → API retrieval) 검증 (느리지만 확실)

### 2. Bootstrap DI 패턴

#### Production (src/modules/news/bootstrap.py)
```python
def get_repository(
    session: Annotated[Session, Depends(get_session)],
) -> NewsRepositoryPort:
    """Repository provider.
    
    Production: PgNewsRepository (request-scoped session).
    Test: app.dependency_overrides 로 override.
    """
    return PgNewsRepository(session)


async def setup_news_collector() -> AsyncioSchedulerAdapter:
    """Scheduler + NewsCollectorService 초기화.
    
    매 실행마다 새 session 생성 (per-execution isolation).
    """
    scheduler = AsyncioSchedulerAdapter()
    
    async def run_collector() -> None:
        session = Session(get_engine())  # ← Per-execution
        try:
            repository = PgNewsRepository(session)
            collector = NewsCollectorService(...)
            await asyncio.to_thread(collector.run, ...)
        finally:
            session.close()  # ← 확실한 정리
    
    scheduler.schedule(run_collector, interval_seconds=interval)
    return scheduler
```

#### Test (tests/integration/news/conftest.py)
```python
@pytest.fixture
def pg_client_with_news_data(pg_with_news_data, news_pg_repository):
    """GET /news 테스트용 TestClient (Real DB + Real Repository).
    
    DI override: get_repository → news_pg_repository (pg_session fixture).
    """
    app.dependency_overrides[get_repository] = lambda: news_pg_repository
    return TestClient(app)
```

**Key**: Production 은 bootstrap 함수로 주입, Test 는 conftest fixture 로 override.

### 3. Per-Execution Session

**Production**:
```python
async def run_collector() -> None:
    session = Session(get_engine())  # 매 scheduler tick 마다 새 session
    try:
        repository = PgNewsRepository(session)
        collector = NewsCollectorService(..., repository=repository)
        await asyncio.to_thread(collector.run, ...)
    finally:
        session.close()  # 즉시 정리 (connection pool 복귀)
```

**이점**:
- Scheduler 가 여러 번 실행돼도 connection pool 고갈 안 함
- Session state isolation (각 실행이 독립적)
- finally 보증 (exception 후에도 정리)

**Test**:
```python
@pytest.fixture
def pg_with_news_data(pg_session):
    """Test fixture: transaction 격리 (rollback)."""
    # pg_session = test 시작 시 connection + transaction begin
    # test 종료 시 rollback (새 test 는 깨끗한 상태)
    return pg_session
```

**이점**:
- Test 간 DB state 격리 (transaction 롤백)
- Per-execution session 처럼 isolation 제공하지만, 명시적 (test fixture)

## Rationale

1. **3계층 이유**:
   - Unit: 빠르고 격리됨 (개발자 피드백)
   - Integration: 신호 (Scheduler, Mock API 동작)
   - System: 진정한 E2E (프로덕션 경로 검증)
   - **결과**: 테스트-프로덕션 gap 감지 ✅

2. **Bootstrap 함수 이유**:
   - DI container 로서 책임 명확 (production 는 bootstrap, test 는 override)
   - Per-execution session 생성 위치 (scheduler callback 내부)
   - Test 도 같은 port 사용 (Repository 인터페이스 일관성)

3. **Per-Execution Session 이유**:
   - Connection pool exhaustion 방지
   - Scheduler 장시간 운영 시 session leak 방지
   - Test 와 동일한 격리 전략 (각각 new session 생성)

## Test-Prod Parity Checklist

**테스트와 프로덕션 간 일관성 확보**:

- [ ] Mock API 응답 구조 = Real API (responses mock 이 Real API response 를 모사)
- [ ] Repository 구현체 = Real (System acceptance 는 pg_session fixture 사용)
- [ ] Scheduler 로직 = 실제 (AsyncioSchedulerAdapter 사용, mock 아님)
- [ ] Session lifecycle = 일관성 (production: per-execution close, test: fixture rollback)

**미충족 시 발생하는 문제**:
```
예: Mock API 응답 필드명 ≠ Real API
→ Unit/Integration test green
→ Production API call failure ❌
```

## Migration Path

### PR #22 완료 후 (현재)
- ✅ 3계층 test 패턴 수립
- ✅ bootstrap DI 패턴 검증
- ✅ Per-execution session 구현
- ✅ System acceptance test 추가

### 다음 slice (news-retrieval 관련)
- [ ] testing.md 강화 (mock 유지보수 규칙 추가)
- [ ] System acceptance test 를 모든 slice 의 accept 기준으로 고정
- [ ] Mock API response 구조 sync 자동화 검토 (OpenAPI spec 활용)

## References

- [ADR 2026-07-06 repository-strategy](./2026-07-06-repository-strategy.md) — Port 추출, Fake vs Real
- [testing.md](../../concenews-backend/docs/conventions/testing.md) — Test 계층 규칙
- [plan-news-collection.md](../../concenews-backend/docs/plan-news-collection.md) — News collection 설계
- FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/
- SQLAlchemy session: https://docs.sqlalchemy.org/en/20/orm/session.html
