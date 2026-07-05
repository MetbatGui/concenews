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
     "id": "UUID v7 문자열 (예: 01912345-6789-7abc-8def-0123456789ab)",
     "title": "string",
     "description": "string",
     "link": "string",
     "source": "string",
     "published_at": "ISO8601 datetime",
     "keywords": "string (쉼표 구분)",
     "categories": ["string"]
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

### 데이터 소스: TheNewsAPI

**선택 이유:**
- 저비용 ($9/month Basic)
- 충분한 Rate (2,500 req/day, 15분마다 수집 가능)
- 신뢰 언론사 (CBS News 등)
- 실시간 업데이트

**API 명세:**
```
GET https://api.thenewsapi.com/v1/news/top
?api_token={token}
&search={keyword}
&locale=us
&limit=10
```

**응답 필드 → NewsItem 맵핑:**
| API Field | NewsItem | 설명 |
|-----------|----------|------|
| uuid (외부 API 고유값) | (참조 안 함) | Domain id 는 IdGenerator 가 자체 발급 (UUID v7). 외부 uuid 는 dedup 용 link 로 대체. |
| title | title | 기사 제목 |
| description | description | 요약 (자동 생성) |
| url | link | 기사 링크 |
| source | source | 출처 (cbsnews.com 등) |
| published_at | published_at | ISO8601 시간 |
| keywords | keywords | 쉼표 구분 텍스트 (필터링용) |
| categories | categories | 카테고리 배열 (참고용) |

**수집 전략:**
- 키워드: 개별 검색 (OR 조합 대신)
  - "interest rate" (32,202건)
  - "forex" (921건)
  - "currency" (16,130건)
  - "Fed rate decision" (3,484건)
- 주기: 15분마다 1회 (무료: 100 req/day, Basic: 2,500 req/day)
- 중복 제외: `link` (원본 URL) 기준 (외부 API uuid 는 참조 안 함, Domain id 는 자체 UUID v7 발급)

**데이터 품질:**
- ✓ 신뢰 언론사 (CBS News, Yahoo)
- ✓ 실시간 (수 분 내)
- ⚠️ keywords 필드: 때로 비어있음
- ⚠️ categories 필드: 자동 추출 (정확도 낮음) → 현재 사용 안 함

**참고:** [spikes/news_spikes/LEARNINGS.md](../spikes/news_spikes/LEARNINGS.md)

### 저장소
- Python dict/list (메모리, 테스트용)
- 향후: PostgreSQL + Redis 캐싱

---

## 구현 상태

1. ✓ **Spike** 완료: 뉴스 API 선택 (TheNewsAPI)
2. ✓ **Spec** 정의: 이 문서
3. ✓ **Plan** 완료: 6단계 PR 구성 ([plan-news-fetch.md](plan-news-fetch.md))
4. → **Implementation**: TDD 개발 중 (feature/news-fetch-*)
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
      "id": "01912345-6789-7abc-8def-0123456789ab",
      "title": "Bessent on Trump's crypto earnings, Trump Accounts and the U.S. economy's struggles",
      "description": "Treasury Secretary Scott Bessent touched on the recent disclosure of President Trump's crypto earnings...",
      "link": "https://www.cbsnews.com/news/scott-bessent-trump-crypto-earnings-trump-accounts-inflation/",
      "source": "cbsnews.com",
      "published_at": "2026-07-03T01:56:53Z",
      "keywords": "Scott Bessent, Economy, Donald Trump, Inflation",
      "categories": ["general", "politics"]
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
src/modules/news/
  ├─ endpoints.py       (FastAPI route)
  ├─ services.py        (비즈니스 로직)
  ├─ domain.py          (NewsItem 모델)
  └─ repositories.py     (저장소)
```

### 테스트 전략

- **Acceptance**: GET /news walking skeleton 1개
  - endpoint 200 + GetNewsResponse schema 유효
- **Integration**: fixture 기반 시나리오 (wire-up 후)
  - 빈 상태, 필드 검증, count 매칭, limit, 정렬 등
- **Unit**: Domain, Service, Repository
- **현재 상태**: RED phase (404 - 구현 전)

## 다음 단계

1. ✓ Spike & Plan
2. → Refactor & Code Review
3. → Merge to master
4. → Spike #2: NewsAPI 통합 (데이터 수집)
