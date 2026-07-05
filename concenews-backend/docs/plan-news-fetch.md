# Plan: 뉴스 조회 기능

> 설계 (Spec 기반)
> Endpoint → Service → Domain → Repository 4계층 구조

---

## 아키텍처

### 1. Endpoint (FastAPI)

```python
GET /news
  Response: {
    "news": [NewsItem],
    "count": int
  }
```

**책임**: HTTP 변환 (Request/Response)

### 2. Service (Business Logic)

```
NewsService
  - fetch_news() → List[NewsItem]
  - 역할: NewsAPI 호출, 데이터 변환, Domain 모델 생성
```

**책임**: 비즈니스 로직 (NewsAPI 통합, 데이터 정규화)

### 3. Domain (Business Rules)

```
NewsItem (Pydantic)
  - id: int             (필수, IdGenerator 발급)
  - title: str          (min_length=1)
  - description: str | None
  - link: str           (min_length=1, dedup key)
  - source: str         (min_length=1)
  - published_at: datetime  (ISO8601 파싱)
  - keywords: str       (default "")
  - categories: list[str]   (default [])
```

**책임**: 도메인 규칙 (필드 검증, 변환)

**ID 전략**: bigint sequence, `IdGenerator` (infra port) 발급.
Domain 은 생성 시점부터 id 소유 (DDD). 상세는
[ADR 2026-07-04 id-strategy](../../docs/decisions/2026-07-04-id-strategy.md) 참고.

**현재 상태**: Anemic (data + validation 만). **의도적**.
- 이 slice 의 use case (조회/정렬/limit) 는 domain method 요구 안 함
- 정렬 = Service/Repository, dedup = Repository (link key)
- YAGNI: 지금 method 넣으면 speculative

**Behavior 유입 트리거** (다음 slice 이후):
- `matching` slice: `NewsItem.matches(market_signal)` 등 매칭 로직
- 카테고리 필터 use case: `NewsItem.belongs_to(category)`
- 최신 판정 use case: `NewsItem.is_recent(now)`

**Anemic 고착화 방지 규칙**: Service 에서 domain state 를 조작하는 로직 발견 시 → NewsItem 메서드로 이전 (refactor).

### 4. Repository (Data Access)

```
NewsRepository
  - store(news: NewsItem) → None
  - get_all() → List[NewsItem]
  - 저장소: dict (메모리)
```

**책임**: 데이터 접근 (메모리 저장소)

---

## 데이터 흐름

```
Endpoint (FastAPI route)
  ↓
Service.fetch_news()
  ├─ NewsAPI 호출 (requests)
  ├─ 응답 파싱
  └─ NewsItem 생성 (Domain)
  ↓
Repository.store() (메모리 저장)
  ↓
Endpoint 응답 반환
```

---

## 폴더 구조 (Modular Monolith)

```
concenews-backend/
├─ src/
│  └─ modules/
│     └─ news/
│        ├─ endpoints.py     (GET /news route)
│        ├─ services.py      (NewsService, NewsAPI 통합)
│        ├─ domain.py        (NewsItem - Pydantic)
│        └─ repositories.py   (NewsRepository - 메모리 저장소)
├─ tests/
│  ├─ integration/
│  │  └─ test_news_fetch.py
│  └─ unit/
│     ├─ test_news_fetch_service.py
│     ├─ test_news_fetch_domain.py
│     └─ test_news_fetch_repository.py
```

### 설계 고려사항
- 각 Slice (news-fetch, market-info, matching...)는 **독립적인 모듈**
- Domain 세분화 필요 시 (Entity, VO) → `domain/entities.py`, `domain/vos.py` 로 분리 가능
- 현재: NewsItem 1개만 → 단순 유지 (YAGNI)

---

## TDD 순서 & PR 구성

**원칙**: 각 PR = 하나의 walking skeleton 또는 계층 완결 (RED + GREEN + Refactor).
Merge 시 master 는 항상 green.

### PR #1: Walking Skeleton — `feature/news-fetch-acceptance`
- Acceptance test 1개 (200 + schema)
- Stub endpoint (`news=[], count=0`)
- 상태: **GREEN**

### PR #2: Domain — `feature/news-fetch-domain`
- `NewsItem` Pydantic 모델
- Unit test (필드 검증)
- 상태: **GREEN**

### PR #3: Repository — `feature/news-fetch-repository`
- `InMemoryNewsRepository` (initial 파라미터 생성자, save 는 upsert)
- Unit test 5개 (fixture 없이 직접 생성 — YAGNI)
- Fixture (`filled_repository` / `empty_repository`) 는 **wire-up PR** 로 이관
  (integration test 에서 실제 사용처 등장 시)
- 상태: **GREEN**

### PR #4: Service — `feature/news-fetch-service`
- `NewsService.fetch_news(limit)`
- Unit test (limit, 정렬)
- 상태: **GREEN**

### PR #5: Wire up + Integration — `feature/news-fetch-wire`
- Endpoint → Service/Repository 연결 (FastAPI DI)
- **Request DTO 도입**: `GetNewsRequest(BaseModel)` — `limit: int = Field(50, ge=1, le=100)`
  - 이유: Response DTO (`GetNewsResponse`) 와 대칭, 계약 명시, param 확장 대비, portfolio DDD 준수
  - Layered validation: adapter (endpoint) = boundary check. Service 는 valid 가정.
- Fixture 도입: `filled_repository` / `empty_repository` (`tests/unit/news/conftest.py` 또는 integration 위치)
- Fixture 기반 integration test (empty, filled, sorted, limit 등)
- 마지막 PR body 에 `Closes #{issue}` 포함
- 상태: **GREEN** (전체 slice 완료)

**Request DTO vs Query direct — 결정 근거**:
- FastAPI idiomatic 은 Query direct 지만 이 프로젝트는 Response DTO 이미 있음 → 대칭 이득
- Param 성장 예상 (filter, since, keyword 등) → DTO 가 확장 흡수 easy
- Custom validator 여지 (예: keyword 정규화)
- Layered architecture (DDD/hexagonal) 준수 신호
- Trade-off: 1개 param 에 클래스 하나 = borderline over, 하지만 대칭/확장으로 정당화

---

## 이전 접근의 실수 (참고)

**초기 계획: 7 PR** (acceptance-test → stub → domain → repo → service → wire → close):
- PR #1 (acceptance-test only) merge 시 master 가 RED 됨 → "master 항상 green" 위반
- Trivial PR 남발 → process overhead

**결정**: RED-only PR 분리 금지. TDD cycle 결합.
결정 이력: master merge commits `72158c6` (TDD 원칙 재설계),
그리고 stub PR (walking skeleton 결합 반영).

---

## 의존성

```
FastAPI (이미 설치됨)
Pydantic (이미 설치됨)
requests (필요 시 설치)
pytest (테스트)
httpx (테스트용 client)
```

---

## 향후 확장

- [ ] 다중 뉴스 소스 지원 (NewsSource 인터페이스)
- [ ] 캐싱 (Redis)
- [ ] 필터링 (카테고리, 키워드)
- [ ] 페이지네이션
- [ ] PostgreSQL 마이그레이션
