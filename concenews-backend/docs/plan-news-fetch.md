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
│     └─ news_fetch/
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

## TDD 순서

### Phase 1: Integration Test
```python
# GET /news 호출 → NewsItem[] 반환 검증
def test_get_news_returns_items():
    response = client.get("/news")
    assert response.status_code == 200
    assert "news" in response.json()
    assert isinstance(response.json()["news"], list)
```

### Phase 2: Unit Tests
1. NewsItem 검증 (Domain)
2. NewsService.fetch_news() (Service)
3. NewsRepository (Repository)

### Phase 3: Implementation
- Walking Skeleton (최소 구현)
- Refactoring

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
