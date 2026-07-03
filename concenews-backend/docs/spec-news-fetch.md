# Spec: 뉴스 조회 기능

## 사용자 스토리

개발자로서, 금리/통화 관련 주요 뉴스를 조회할 수 있어야 한다.
향후 이 뉴스 데이터를 마켓 정보와 매칭하는 기초가 됨.

---

## Acceptance Criteria

1. **GET /news** 호출 시 최근 뉴스 목록 반환 (최대 50개)
   - 응답: 200 OK
   - 정렬: published_at 최근순

2. **뉴스 필드**
   ```json
   {
     "id": "uuid",
     "title": "string",
     "description": "string",
     "link": "string",
     "source": "string",
     "published_at": "ISO8601 datetime"
   }
   ```

3. **저장된 뉴스가 없으면** 빈 배열 반환 (`[]`)

4. **응답 형식**
   ```json
   {
     "news": [
       { /* NewsItem */ },
       { /* NewsItem */ }
     ],
     "count": 2
   }
   ```

---

## Out of Scope (이 기능에선 다루지 않음)

- 실시간 뉴스 크롤링/갱신 (Spike로 검토, 별도 기능)
- 뉴스 필터링 (카테고리, 키워드)
- 페이지네이션
- 뉴스 저장소 영속성 (메모리만 사용)

---

## 기술 결정

- **데이터 소스**: TheNewsAPI Basic ($9/month, 2,500 req/day)
  - Query: `interest rate OR forex OR currency`
  - 수집 주기: 15분마다 1회 (96 req/day)
  - 참고: [spikes/news_spikes/LEARNINGS.md](../spikes/news_spikes/LEARNINGS.md)
- **저장소**: Python dict/list (메모리, 테스트용)
- **향후 마이그레이션**: PostgreSQL + Redis 캐싱

---

## 구현 상태

1. ✓ **Spike** 완료: 뉴스 API 선택 (TheNewsAPI)
2. ✓ **Spec** 정의: 이 문서
3. ✓ **Plan** 완료: 6단계 PR 구성 ([plan-news-fetch.md](plan-news-fetch.md))
4. → **Implementation**: TDD 개발 중 (feature/news-fetch)
   - ✓ Phase 1: Domain (NewsItem)
   - ✓ Phase 2: Repository (메모리 저장소)
   - ✓ Phase 3: Service (비즈니스 로직)
   - ✓ Phase 4: Endpoint (GET /news)
   - → Phase 5: Refactor (진행 예정)
   - → Phase 6: Close Issue

## 구현 세부사항

### API 엔드포인트

```
GET /news?limit=50
```

**쿼리 파라미터:**
- `limit` (int, 선택): 반환할 최대 기사 수 (1-100, 기본값: 50)

**응답 (200 OK):**
```json
{
  "news": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Interest Rate Decision Announced",
      "description": "Central bank raises rates by 0.25%",
      "link": "https://example.com/article",
      "source": "Reuters",
      "published_at": "2026-07-03T10:00:00Z"
    }
  ],
  "count": 1
}
```

### 아키텍처 (DDD 4계층)

```
Endpoint (HTTP)
    ↓ Request
Service (Business Logic)
    ↓ Domain Model
Domain (NewsItem - Pydantic)
    ↓ Persistence
Repository (Memory Dict)
```

**파일 구조:**
```
src/modules/news_fetch/
  ├─ endpoints.py       (FastAPI route)
  ├─ services.py        (비즈니스 로직)
  ├─ domain.py          (NewsItem 모델)
  └─ repositories.py     (저장소)
```

### 테스트 전략

- **Integration**: GET /news 응답 검증 (6 tests)
- **Unit**: Domain, Service, Repository (17 tests)
- **현재 상태**: 23/23 PASSED

## 다음 단계

1. ✓ Spike & Plan
2. → Refactor & Code Review
3. → Merge to master
4. → Spike #2: NewsAPI 통합 (데이터 수집)
