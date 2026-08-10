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
- `test_{module}_collection_integration.py` — 외부 HTTP fixture + 실 DB 통합
- `test_{module}_collection_real_api.py` — 실제 외부 API + 실 DB E2E (`@pytest.mark.e2e`)
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

## Classicist 테스트 전략

상세 결정은 [ADR 2026-08-09 classicist-test-strategy](../../../docs/decisions/2026-08-09-classicist-test-strategy.md)를 따른다.

- Domain, Application, Repository는 가능한 실제 구현체를 조합하고 반환값·저장 상태를 검증한다.
- HTTP, 시간, 스케줄러 같은 프로세스 밖 경계만 결정적 Fake 또는 Transport로 대체한다.
- 실제 외부 API와 실제 DB를 함께 쓰는 테스트만 `@pytest.mark.e2e`로 표시한다.
- 외부 API mock 응답은 `tests/fixtures/`의 버전 관리 fixture를 사용한다. Spike에서 응답 계약을 다시 확인하면 fixture부터 갱신한다.

### 경계별 선택 기준

| 대상 | 기본 선택 | 검증 방식 |
|---|---|---|
| Domain·Application·Repository | 실제 구현체 조합 | 반환값·저장 상태·관찰 가능한 결과 |
| PostgreSQL | Integration에서 실제 컨테이너 | 실제 SQL과 스키마 |
| 외부 HTTP | fixture 기반 Transport/Fake | 요청 계약과 변환 결과 |
| 시간·주기 대기 | 제어 가능한 시간 또는 수동 trigger | `sleep` 없이 결과 상태 |
| 실제 외부 API | 수동 E2E | `@pytest.mark.e2e` + 실제 DB |

- 내부 구현의 호출 횟수·순서·private 메서드는 assertion 대상이 아니다.
- 외부 HTTP fixture는 테스트 안에 다시 쓰지 않는다. `tests/fixtures/`에서 import해 사용한다.
- Acceptance는 사용자 관점의 **Integration 테스트 하위 유형**이다. 외부 API가 Fake이면 전체 경로를 통과해도 E2E가 아니다.

## 검증

병합 전:
```bash
just check-branch-green
```

실제 외부 API는 배포 전 수동으로 검증한다.

```bash
THENEWSAPI_TOKEN=your_api_key just check-e2e
```

`check-branch-green`은 `e2e` 마커를 제외하므로 빠르고 결정적이다. AGENTS.md "코드 편집 후 필수 검증" 규칙 참고.

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

### 테스트 분류

각 계층의 Repository 선택:

| 계층 | 파일 | Repository | 속도 | 검증 대상 |
|------|------|-----------|------|---------|
| **Unit** | `test_service.py` | 상태를 가진 단순 Fake 허용 | 빠름 | 규칙·분기·예외 |
| **Integration** | `test_..._integration.py` | 실제 `Pg...Repository` + 실제 DB | 보통 | 컴포넌트 협력과 DB 계약 |
| **Acceptance** | `test_..._acceptance.py` | Integration과 동일 | 보통 | HTTP 사용자 시나리오 |
| **E2E** | `test_..._real_api.py` + `@pytest.mark.e2e` | 실제 외부 API + 실제 DB | 가변 | 외부 계약과 전체 저장 흐름 |

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
- 외부 API 경계를 대체하되, 상호작용 횟수가 아니라 저장 상태를 검증한다.

### Integration Test + Real DB (pg_session fixture)

```python
# tests/integration/news/test_news_collection_integration.py
class TestNewsCollectionIntegration:
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

### Acceptance Test (전체 HTTP 경로)

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
- 사용자 관점 invariant 검증 (정렬, 필드 무결성). 외부 API가 Fake이므로 E2E가 아니다.

### 외부 HTTP Fixture 동기화 필수 ⚠️

**중요**: Fixture와 실제 API 응답 구조가 다르면 test green ≠ production working. 모든 테스트는 `tests/fixtures/`의 버전 관리 fixture를 사용한다.

```python
# ❌ 잘못된 예: Test 에서만 되는 구조
with responses.RequestsMock() as rsps:
    rsps.add(
        responses.GET,
        "https://api.thenewsapi.com/v1/news",  # ← 잘못된 endpoint
        json={"articles": [...]},  # ← 잘못된 응답 key
    )

# ✅ 올바른 예: Fixture로 Real API 계약을 재사용
with responses.RequestsMock() as rsps:
    rsps.add(
        responses.GET,
        "https://api.thenewsapi.com/v1/news/top",  # ← Real endpoint
        json=THENEWSAPI_TOP_RESPONSE,  # ← tests/fixtures/에서 import
    )
```

**검증 방법**:
1. Spike 단계에서 Real API 응답을 확인하고 `docs/research/`에 기록
2. Research 결과를 바탕으로 `tests/fixtures/` fixture 갱신
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
THENEWSAPI_TOKEN=your_key just check-e2e
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
