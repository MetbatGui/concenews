# News Source Spike: Learnings & Decision

## Question

어떤 뉴스 API를 사용하여 금리/통화 뉴스를 수집할 것인가?

요구사항:
- 금융 뉴스 커버리지
- 무료 또는 저비용 (프로토타입 단계)
- API 안정성 및 응답 속도

---

## Candidates Evaluated

1. **NewsAPI.org** (`newsapi_spike.py`)
2. **Reuters RSS** (`reuters_rss_spike.py`)
3. **NewsAPI.ai** (`spike_newsapi_ai.py`)
4. **Alpha Vantage News** (`alpha_vantage_spike.py`)
5. **NewsAPI Hourly Volume** (`spike_newsapi_volume.py`)
6. **TheNewsAPI** (external research)
7. **Thunderbit** (external research, excluded)

---

## Findings

### NewsAPI.org

**테스트 결과:**
- Status: ✓ 성공
- 응답: JSON (명확한 구조)
- 기사 수: 5,547개 (금융 소스 12개 필터)
- pageSize: 10 확인 (증가 가능 여부 미확인)
- 필드: `title`, `source`, `datePublished`, `body`, 메타데이터

**장점:**
- 응답 구조 명확
- 금융 뉴스 다양 (Reuters, Bloomberg, CNBC 등)
- 국제 뉴스 소스 풍부

**제약:**
- 무료: 100 req/day (→ 5분마다 1회 = 288 req/day 요구 불충족)
- 프로덕션: $449/month
- CORS 이슈 (프로덕션 도메인 확인 필요)

---

### Reuters RSS

**테스트 결과:**
- Status: ✓ 성공 (ir.thomsonreuters.com)
- 응답: XML 피드 (feedparser 파싱)
- 항목 수: News Releases + Events만 (금융뉴스 약함)
- 기사 필드: `title`, `link`, `published`, `summary`

**장점:**
- Rate limit 없음 (무제한 요청)
- 구현 간단 (RSS 표준)
- 외부 API Key 불필요

**제약:**
- 금융 뉴스 약함 (회사 공시 중심)
- 국제 금융 뉴스 부족
- 피드 개수 제한 (ir.thomsonreuters.com만 금융)

---

### NewsAPI.ai

**테스트 결과:**
- Status: ✗ 불가능
- 이유: 학교/비즈니스 이메일 가입만 허용
- 가입 불가

**특징:**
- AI 기반 뉴스 큐레이션
- 고급 필터링 (주제, 감정 분석)
- 프로덕션 지향

---

### Alpha Vantage News

**테스트 결과:**
- Status: ✓ 성공
- API: `NEWS_SENTIMENT` 엔드포인트
- 응답: JSON
- 항목 필드: `title`, `url`, `time_published`, `summary`, `source`, `overall_sentiment_score`

**장점:**
- 감정 분석 포함 (sentiment_score)
- 금융 주제 필터링 가능 (CURRENCY, FINANCE)
- API 안정성

**제약:**
- 무료: 500 req/day (충분하지만 제한적)
- 금융 뉴스 커버리지 확인 필요
- 기사 개수 적을 가능성

---

### NewsAPI Hourly Volume

**테스트 결과:**
- Status: ✗ from/to 범위 지정 시 0개 반환
- 원인: 날짜 형식 또는 범위 설정 오류
- 대체: 전체 조회로 회피

**시사점:**
- 시간대별 필터링 복잡
- 일일 수집 전략으로 대체 (from/to 제외)

---

### TheNewsAPI (외부 조사)

**특징:**
- Basic 플랜: $9/month
- Rate: 2,500 req/day
- 응답 속도: 100-200ms (빠름)
- CORS: 문제 없음
- 기사 개수: Basic은 25 articles/req → 62,500 articles/day (충분)

**장점:**
- 저비용 ($9/month)
- 충분한 Rate (일 96회 = 15분마다 1회)
- 구현 간단
- 안정성 검증됨

**제약:**
- 무료 플랜: 3 articles/req만 (프로토타입 불가)
- Basic 플랜 가입 필요

---

### Thunderbit (외부 조사, 제외됨)

**특징:**
- $16/month
- AI 기반 뉴스 필터링
- 강력한 큐레이션

**제외 사유:**
- 사용자 결정: "선더빗에서 난 기사들은제외"
- 비용 대비 이점 불충분

---

## Decision: TheNewsAPI (Basic $9/month)

### Why

1. **비용 최적**: $9/month (프로토타입 → 운영으로 확장 시 $16, $49 옵션도 있음)
2. **충분한 Rate**: 2,500 req/day = 일 96회 (15분마다 1회)
   - 요구: 288 req/day (5분마다) → 15분마다로 조정 가능
3. **구현 간단**: REST API, JSON 응답
4. **안정성**: 상용 API 검증됨
5. **CORS 문제 없음**: 백엔드에서 직접 호출 가능
6. **NewsAPI.org vs**: 무료 한계(100 req/day) 해결, CORS 이슈 해결

### Implementation Notes

- API: `https://www.thenewsapi.com/v1/news/top`
- Query: `q=interest rate OR forex OR currency` + `country=us,gb,de,jp,cn` 등
- Rate: 15분마다 1회 스케줄 작업
- Caching: 수집 기사 DB 저장 (중복 제외)
- Response: 25 articles/req → newsItem 변환

---

## 다음 단계

1. spec-news-fetch.md 업데이트: "데이터 소스: TheNewsAPI (Basic)"
2. Spike 코드 삭제 (LEARNINGS.md만 유지)
3. GitHub Milestone: news-fetch
4. GitHub Epic Issue: [news-fetch] 뉴스 조회 Slice
5. feature/news-fetch 브랜치 생성
6. Integration Test 작성 (GET /news 응답 검증)
7. TDD 개발 시작
