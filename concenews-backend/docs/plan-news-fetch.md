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

### PR #1: Acceptance Test (RED) — `feature/news-fetch-acceptance-test`
- Acceptance test 1개: endpoint 200 + GetNewsResponse schema 유효
- Schema Contract 정의 (GetNewsResponse, NewsItemResponse)
- 실패 확인 (404)

### PR #2: Stub Endpoint (GREEN) — `feature/news-fetch-endpoint-stub`
- `/news` endpoint 최소 응답 (`news=[], count=0`)
- Acceptance test 통과

### PR #3: Domain — `feature/news-fetch-domain`
- `NewsItem` Pydantic 모델
- Unit Test (필드 검증, 변환)

### PR #4: Repository — `feature/news-fetch-repository`
- `InMemoryNewsRepository` (initial dict 받는 생성자)
- Unit Test
- `filled_repository` / `empty_repository` fixture 정의

### PR #5: Service — `feature/news-fetch-service`
- `NewsService.fetch_news(limit)`
- Unit Test (limit, 정렬)

### PR #6: Wire up + Integration — `feature/news-fetch-wire`
- endpoint 를 Service/Repository 에 연결 (FastAPI DI)
- 추가 integration test (fixture 활용):
  - `test_empty_when_no_articles` (empty fixture)
  - `test_article_fields` (filled fixture)
  - `test_sorted_by_published_at_desc` (filled fixture)
  - `test_limit_parameter`, `test_default_limit_50`, `test_max_50`
- Acceptance 여전히 green

### PR #7: Close Issue — `feature/news-fetch-close`
- Closes #{issue} (자동 close)

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
