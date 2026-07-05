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

## 참고

- [docstring.md](docstring.md) — Google Style + GWT
- [immutability.md](immutability.md) — Domain frozen/tuple test 패턴
- [xp.md](../../../docs/architecture/principles/xp.md) — TDD 순서
