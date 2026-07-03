# Spec: 뉴스 조회 기능

## 사용자 스토리

**주요 사용자**: 트레이더, 투자자, 금융에 관심있는 일반인

**스토리**:
> 금리와 환율 변동에 영향을 미치는 주요 뉴스를 빠르게 조회하고 싶다.
> 최신 뉴스를 통해 시장 이동을 예측하고 투자 결정에 활용할 수 있도록.

**목표**: 금리/환율/통화 관련 뉴스 + 실시간 마켓 데이터를 연결해 
> "뉴스 → 마켓 영향" 흐름 파악

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
