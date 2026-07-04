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
  - id: str
  - title: str
  - description: str
  - link: str
  - source: str
  - published_at: datetime
```

**책임**: 도메인 규칙 (필드 검증, 변환)

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
- `InMemoryNewsRepository` (initial dict 생성자)
- Unit test + `filled_repository` / `empty_repository` fixture
- 상태: **GREEN**

### PR #4: Service — `feature/news-fetch-service`
- `NewsService.fetch_news(limit)`
- Unit test (limit, 정렬)
- 상태: **GREEN**

### PR #5: Wire up + Integration — `feature/news-fetch-wire`
- Endpoint → Service/Repository 연결 (FastAPI DI)
- Fixture 기반 integration test (empty, filled, sorted, limit 등)
- 마지막 PR body 에 `Closes #{issue}` 포함
- 상태: **GREEN** (전체 slice 완료)

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
