# Test 구조 & 위치 규칙

> pytest 기반. 모듈 별 폴더 + 성격 별 파일.

---

## 폴더 구조

```
tests/
├── conftest.py                  ← 공통 fixture (unit + integration 모두 사용)
├── unit/
│   ├── conftest.py              ← unit 만 사용
│   └── {module}/
│       ├── conftest.py          ← 모듈 unit 전용
│       ├── test_domain.py       ← Domain 모델 검증
│       ├── test_repository.py   ← Repository 검증
│       └── test_service.py      ← Service 검증
└── integration/
    ├── conftest.py              ← integration 만 사용 (client, filled_repo 등)
    └── {module}/
        └── test_{module}_acceptance.py  ← endpoint 시나리오
```

`{module}` = news, market, matching 등.

---

## 파일명 규칙

### Unit
- `test_domain.py` — 도메인 모델
- `test_repository.py` — 저장소
- `test_service.py` — 서비스
- `test_{concept}.py` — 기타 unit (id_generator 등)

### Integration
- `test_{module}_acceptance.py` — endpoint 시나리오 (사용자 관점)
- `test_{module}_repository_postgres.py` — 실 DB 통합 (미래)
- `test_{module}_collection.py` — 외부 API 통합 (미래)
- `test_{module}_{other}_integration.py` — 다른 모듈 통합 (미래)

---

## Acceptance vs Integration

**Integration ⊃ Acceptance**:
- Integration: 여러 컴포넌트 협력 검증 (넓음)
- Acceptance: 사용자 관점 endpoint 시나리오 (좁음, integration 부분집합)

**Web API 프로젝트**:
- 대부분 acceptance = HTTP endpoint test
- Lower-level integration (Repo + DB, 외부 API) 은 별도 파일

---

## Class 그룹핑

같은 파일 안에서 시나리오 성격별 class 로 그룹:

```python
class TestGetNewsWalkingSkeleton:
    """Endpoint 최소 연결 증명."""
    def test_get_news_returns_valid_response(self, client): ...


class TestGetNewsBehavior:
    """세부 behavior (정렬/limit/필드)."""
    def test_returns_empty_when_no_articles(...): ...
    def test_returns_sorted_by_published_at_desc(...): ...
    def test_respects_limit(...): ...
```

---

## Test 격리 (Singleton Cache Clear)

Module-level singleton (예: `@lru_cache` provider) 는 test 간 state 공유 위험.

### 지금 방식 (InMemory)
```python
# tests/conftest.py
@pytest.fixture(autouse=True)
def _clear_singleton_cache():
    yield
    get_repository.cache_clear()
```

- Autouse → 매 test 자동 실행
- Repository singleton 을 매 test 후 재초기화

### 미래 (PG 도입 시)
Transaction rollback fixture 로 대체. Repository 인터페이스 변경 없음.

### 근거
- [ADR 2026-07-05 test-isolation-cache-clear](../../../docs/decisions/2026-07-05-test-isolation-cache-clear.md)
- InMemory 와 PG 는 다른 격리 메커니즘 — Repository 인터페이스 통일 시도는 premature.

---

## Integration Test Fixture Data 패턴 (Object Mother)

Integration test 는 **hardcoded constants** 로 test data 정의. Factory 대신.

### 구조
```python
# tests/integration/{module}/data.py
NEWS_OLD = NewsItem(id=UUID("...-01"), title="오래된 뉴스", ...)
NEWS_MID = NewsItem(id=UUID("...-02"), title="중간 뉴스", ...)
NEWS_NEW = NewsItem(id=UUID("...-03"), title="최신 뉴스", ...)

# tests/integration/{module}/conftest.py
from tests.integration.{module}.data import NEWS_OLD, NEWS_MID, NEWS_NEW

@pytest.fixture
def filled_repository():
    return InMemoryNewsRepository(initial=[NEWS_OLD, NEWS_MID, NEWS_NEW])

# Test 에서 직접 참조
def test_sorted(self, filled_client):
    data = ...
    assert [item.id for item in data.news] == [NEWS_NEW.id, NEWS_MID.id, NEWS_OLD.id]
```

### 장점
- 결정성 (UUID 고정, test 재현 가능)
- Assertion 강도 (상수 직접 비교)
- Cross-conftest import 회피 (pytest 관용 준수)

### Unit test 는 factory 유지
각 파일 `_make_item` 헬퍼로 unique UUID 생성 (uniqueness 검증 필요).

### 근거
- [ADR 2026-07-05 test-fixture-data-pattern](../../../docs/decisions/2026-07-05-test-fixture-data-pattern.md)

---

## Fixture 위치 규칙

**사용 범위별 위치**:

| 범위 | 위치 |
|------|------|
| Unit + Integration 공통 | `tests/conftest.py` |
| Unit 전용 (전체 or 모듈) | `tests/unit/conftest.py` or `tests/unit/{module}/conftest.py` |
| Integration 전용 | `tests/integration/conftest.py` or `tests/integration/{module}/conftest.py` |

**pytest 규칙**: `conftest.py` 는 트리 상위로 propagate. 하위 test 자동 인식.

### 예시

```python
# tests/integration/conftest.py
@pytest.fixture
def client():
    return TestClient(app)


# tests/integration/news/conftest.py
@pytest.fixture
def filled_repository():
    return InMemoryNewsRepository(initial=[_make_item(1), _make_item(2)])

@pytest.fixture
def empty_repository():
    return InMemoryNewsRepository()
```

---

## Docstring & GWT

**모든 test docstring 은 GWT 형식**. 자세한 규칙: [docstring.md](docstring.md)

```python
def test_get_news_returns_sorted(self, client, filled_repository):
    """뉴스는 published_at 내림차순으로 반환된다.

    Given: filled_repository (news 3개 저장)
    When: GET /news
    Then: published_at 내림차순 정렬
    """
```

**Given 은 명시적**: fixture 로 상태 통제. 암묵 상태 가정 금지.

---

## 시간 관련 테스트 (freezegun)

TTL, 스케줄러, 시간 기반 로직은 `freezegun` 으로 시간 조작. `time.sleep()` 제거.

### 설치

```bash
uv pip install freezegun>=1.5.0  # 또는 pyproject.toml [dependency-groups] dev에 추가
```

### 패턴: TTL/Expiry 검증

```python
from freezegun import freeze_time

def test_cache_ttl_expiry():
    """Given: cache with TTL
    When: time elapses past expiry
    Then: item is expired
    """
    with freeze_time("2026-07-06 12:00:00") as frozen_time:
        cache = SomeCache()
        cache.set("key", ttl_seconds=10)
        assert cache.contains("key") is True

        frozen_time.move_to("2026-07-06 12:00:11")  # 11초 경과 → 만료
        assert cache.contains("key") is False
```

### 장점
- Deterministic (실제 시간 의존 없음)
- Fast (sleep 제거)
- CI 환경 안정 (타이밍 문제 없음)

### 참고
- [freezegun docs](https://github.com/spulec/freezegun)
- Example: `tests/unit/news/test_cache_adapter.py`

---

## 검증

Test 편집 후:
```bash
uvx ruff check src tests
uv run ty check src
uv run pytest --ignore=spikes
```

CLAUDE.md "코드 편집 후 필수 검증" 규칙 참고.

---

## 언제 파일 분리?

**같은 파일 유지** (기본):
- Endpoint 시나리오 (walking skeleton + behavior)
- 응집: 같은 endpoint 단위 test

**분리** (트리거 시):
- 성격 다른 integration (실 DB, 외부 API, 모듈 간 이벤트)
- 파일 500+ 라인 (가독성)

---

## Test 계층 심화: Mock vs Real 전략

### 3계층 Test Pyramid

```
         System (E2E)
            ↑
      Integration (신호)
            ↑
         Unit (빠름)
```

각 계층의 Repository 선택:

| 계층 | 파일 | Repository | 속도 | 검증 대상 |
|------|------|-----------|------|---------|
| **Unit** | `test_service.py` | `InMemoryNewsRepository` | ~100ms | Service 로직 (dedup, error) |
| **Integration** | `test_..._e2e.py` | `PgNewsRepository(pg_session)` | ~500ms | Scheduler + API mock + Real DB |
| **System** | `test_..._system_acceptance.py` | `PgNewsRepository(pg_session)` | ~1s | 전체 경로 (collection → retrieval) |

### Unit Test (InMemoryNewsRepository)

```python
# tests/unit/news/test_news_collector_service.py
class TestNewsCollectorServiceLogic:
    """Service 로직만 검증 (dedup, error handling)."""
    
    def test_dedup_on_cache_hit(self):
        """Given: 캐시된 기사
        When: collector.run()
        Then: DB 저장 안 함
        """
        cache = InMemoryCacheAdapter()
        cache.set("link1", ttl_seconds=900)
        
        repository = InMemoryNewsRepository()
        api = Mock(spec=NewsSourcePort)
        api.fetch.return_value = [NewsItem(link="link1", ...)]
        
        collector = NewsCollectorService(api, cache, repository)
        collector.run(keywords=[...])
        
        # Fake 사용 → 검증 빠름 (SQL 없음)
        assert len(repository.find_all()) == 0
```

**특징**:
- 속도 우선
- 로직만 검증 (저장소 구조 무관)
- Mock API 사용 (responses 불필요)

### Integration Test + Real DB (pg_session fixture)

```python
# tests/integration/news/test_news_collection_e2e.py
class TestNewsCollectionE2E:
    """Scheduler + API mock + Real DB 통합."""
    
    async def test_collector_saves_to_db(self, pg_session):
        """Given: API mock, Real PG DB, Scheduler
        When: scheduler.trigger() (manual run)
        Then: API 호출 → DB 저장 (schema 정합성 확인)
        """
        with responses.RequestsMock() as rsps:
            # Mock API = Real API 구조 동기화 필수 ⚠️
            rsps.add(
                responses.GET,
                "https://api.thenewsapi.com/v1/news/top",
                json={
                    "data": [
                        {
                            "title": "Article 1",
                            "url": "https://example.com/1",
                            "source": "Source A",
                            "publishedAt": "2026-07-06T10:00:00Z",
                            "description": None,
                        }
                    ]
                },
                status=200,
            )
            
            api_client = TheNewsAPIClient(api_key="test-key")
            repository = PgNewsRepository(pg_session)
            collector = NewsCollectorService(api_client, cache, repository)
            
            collector.run(keywords=[...])
            
            # Real Repository + Real DB
            items = repository.find_all()
            assert len(items) == 1
            assert items[0].title == "Article 1"
```

**특징**:
- Mock API 는 Real API 응답 구조 모사
- Repository = Real PgNewsRepository (SQL 실행)
- pg_session fixture = transaction 격리 (test 간 DB 독립)
- **목적**: Scheduler + Service 협력 + DB schema 검증

### System Acceptance Test (전체 경로)

```python
# tests/integration/news/test_news_system_acceptance.py
class TestGetNewsSystemAcceptance:
    """전체 흐름: Collector → DB → GET /news."""
    
    def test_get_news_returns_collected_data(self, pg_client_with_news_data):
        """Given: 3개 뉴스 ORM 적재 (예시 데이터)
        When: GET /news
        Then: 적재된 뉴스 조회 + 정렬 확인
        """
        response = pg_client_with_news_data.get("/news")
        assert response.status_code == 200
        
        data = GetNewsResponse.model_validate(response.json())
        assert data.count == 3
        
        # 최신순 정렬 검증
        published_times = [item.published_at for item in data.news]
        assert published_times == sorted(published_times, reverse=True)
```

**fixture 구조**:
```python
@pytest.fixture
def pg_with_news_data(pg_session):
    """예시 뉴스 ORM 적재."""
    repository = PgNewsRepository(pg_session)
    
    # Real API 응답 형태로 ORM 저장
    for raw in [
        {"title": "News 1", "url": "...", "publishedAt": "2026-07-06T12:00:00Z", ...},
        ...
    ]:
        item = api_client._convert_to_news_item(raw)
        repository.save(item)
    
    return pg_session


@pytest.fixture
def pg_client_with_news_data(pg_with_news_data, news_pg_repository):
    """Real DB + Real Repository + API client."""
    # DI override: get_repository → Real Repository (pg_session 포함)
    app.dependency_overrides[get_repository] = lambda: news_pg_repository
    return TestClient(app)
```

**특징**:
- 전체 경로 검증 (UI → API → DB → Repository → DB)
- Real data flow (실제 프로덕션 경로 모사)
- System-level invariant 검증 (정렬, 필드 무결성)

### Mock API 응답 구조 동기화 필수 ⚠️

**중요**: Mock 과 Real API 응답 구조가 다르면 test green ≠ production working

```python
# ❌ 잘못된 예: Test 에서만 되는 구조
with responses.RequestsMock() as rsps:
    rsps.add(
        responses.GET,
        "https://api.thenewsapi.com/v1/news",  # ← 잘못된 endpoint
        json={"articles": [...]},  # ← 잘못된 응답 key
    )

# ✅ 올바른 예: Real API 와 동기화
with responses.RequestsMock() as rsps:
    rsps.add(
        responses.GET,
        "https://api.thenewsapi.com/v1/news/top",  # ← Real endpoint
        json={"data": [...]},  # ← Real response key
    )
```

**검증 방법**:
1. Spike 단계에서 Real API 응답 캡처 (예: spike-news-api.md)
2. Mock 응답 = Spike 응답 구조 (doc comment 로 참조)
3. Real API test 추가 (THENEWSAPI_TOKEN 환경변수 필요)

```python
# tests/integration/news/test_news_collection_real_api.py
def test_collector_real_api_parses_and_saves_to_db(self, pg_session):
    """Given: Real TheNewsAPI (THENEWSAPI_TOKEN 필요)
    When: collector.run() (실제 API call)
    Then: 응답 파싱 + DB 저장 검증
    """
    api_key = os.getenv("THENEWSAPI_TOKEN")
    if not api_key:
        pytest.skip("THENEWSAPI_TOKEN 환경 변수 필요")
    
    api_client = TheNewsAPIClient(api_key=api_key)
    repository = PgNewsRepository(pg_session)
    collector = NewsCollectorService(api_client, cache, repository)
    
    # 실제 API 호출 (속도 낮지만 신뢰도 높음)
    collector.run(keywords=["interest rate"])
    
    items = repository.find_all()
    assert len(items) > 0
    # 실제 응답 구조 검증
    assert items[0].title
    assert items[0].published_at.tzinfo  # timezone aware
```

**실행**:
```bash
# .env 에 THENEWSAPI_TOKEN 설정 후
THENEWSAPI_TOKEN=your_key uv run pytest tests/integration/news/test_news_collection_real_api.py -v
```

---

## 언제 파일 분리?

**같은 파일 유지** (기본):
- Endpoint 시나리오 (walking skeleton + behavior)
- 응집: 같은 endpoint 단위 test

**분리** (트리거 시):
- 성격 다른 integration (실 DB, 외부 API, 모듈 간 이벤트)
- 파일 500+ 라인 (가독성)

---

## 참고

- [docstring.md](docstring.md) — Google Style + GWT
- [immutability.md](immutability.md) — Domain frozen/tuple test 패턴
- [xp.md](../../../docs/architecture/principles/xp.md) — TDD 순서
- [ADR 2026-07-07 di-bootstrap-strategy](../../../docs/decisions/2026-07-07-di-bootstrap-strategy.md) — Test-Prod 이원화 & Mock 동기화
