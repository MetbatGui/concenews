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

### PR #1: Integration Test (RED) — `feature/news-fetch-integration-test`
- 9개 통합 테스트 작성
- Schema Contract 정의 (GetNewsResponse, NewsItemResponse)
- 전체 실패 상태 (구현 전) ✅ 완료

### PR #2: Endpoint Mock (GREEN) — `feature/news-fetch-endpoint-mock`
- `/news` endpoint 하드코딩 mock 반환
- 통합 테스트 9개 모두 통과

### PR #3: Service 추출 — `feature/news-fetch-service`
- `NewsService` 추출 (비즈니스 로직)
- Unit Test 작성
- 통합 테스트 유지

### PR #4: Domain 모델 추출 — `feature/news-fetch-domain`
- `NewsItem` Pydantic 모델 추출
- Unit Test 작성
- 통합 테스트 유지

### PR #5: Repository 추출 — `feature/news-fetch-repository`
- `NewsRepository` 추출 (메모리 저장소)
- Unit Test 작성
- 통합 테스트 유지

### PR #6: Close Issue — `feature/news-fetch-close`
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
