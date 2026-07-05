# Spec: 뉴스 수집 기능

## 사용자 스토리

**주요 사용자**: 트레이더, 투자자, 금융에 관심있는 일반인
(직접 소비자는 GET /news 사용자 — 이 slice 는 그 저장소를 채움)

**스토리**:
> 시스템이 외부 뉴스 소스에서 주기적으로 뉴스를 수집하여 DB 에 저장한다.
> GET /news 요청 시 최신 뉴스가 이미 준비되어 있다.

**목표**: 요청 latency 최소화 (외부 API 대기 없이 DB 조회로 즉시 응답).
불필요한 외부 API 호출 방지 (rate limit 준수, 비용 절약).

---

## Acceptance Criteria

### AC1. 백그라운드 스케줄러
- 앱 시작 시 스케줄러 등록
- 주기: 매 15분 (초기값, 재조정 가능)
- 실행: TheNewsAPI 로 뉴스 fetch 요청

### AC2. Cache 1차 필터 (재요청 방지)
- In-memory cache (dict + TTL)
- Key: link (뉴스 원본 URL)
- Value: NewsItem or sentinel
- TTL: 15분 (기본값, 스케줄러 주기 정합)
- 캐시 hit 시 → skip (외부 API 재요청 없음, DB 저장 시도 없음)
- 캐시 miss 시 → 다음 단계 진행
- **미래 Redis 대체 가능**: `CachePort` 인터페이스로 추상화

### AC3. DB 2차 검증 (영구 저장)
- PostgreSQL 저장 (persist)
- Unique constraint: link
- Insert 시도 → 성공 시 cache 에 추가
- Duplicate (unique violation) → skip (silent, DB 우선)

### AC4. Fetch 흐름
```
Scheduler tick
   ↓
TheNewsAPI fetch (여러 키워드: "interest rate", "forex", ...)
   ↓
Each item:
   ├─ Cache 확인 (link 기준)
   │   ├─ Hit → skip
   │   └─ Miss → 계속
   ├─ DB insert 시도 (unique link)
   │   ├─ Success → cache 에 추가
   │   └─ Conflict → skip
```

### AC5. 에러 처리
- 외부 API 실패 (timeout, rate limit) → 로그 남기고 skip (다음 tick 재시도)
- DB 실패 (connection error) → 로그
- 개별 item 실패 → 다른 item 진행 (부분 성공 허용)

### AC6. GET /news 는 변경 없음
- 기존 endpoint 유지
- Repository 는 InMemory → PgNewsRepository 로 교체
- GET /news 는 항상 DB 조회 (cache 는 collection 전용)

---

## Out of Scope

- 실시간 push (WebSocket, SSE)
- 사용자별 필터링 (개인화)
- 카테고리/키워드 검색 endpoint
- Cache 통계 대시보드
- Multi-tenant (여러 유저 별 캐시)

---

## 기술 결정 (Spike 후 확정 예정)

### DB
- SQLAlchemy 2.0 async / sync (spike 필요)
- PostgreSQL
- Alembic migration
- ADR 예정

### Cache
- In-memory: `cachetools.TTLCache` 또는 stdlib `dict` + timestamp
- 인터페이스: `CachePort` (`get`, `set`, `contains`) 로 추상화
- Redis 대체 시 `RedisAdapter` 만 교체

### Scheduler
- 후보: APScheduler / FastAPI-scheduler / stdlib `asyncio.create_task` + loop
- Spike 필요
- ADR 예정

### 외부 API
- TheNewsAPI (기존 spike 확정)
- Rate limit: Basic 2,500 req/day (여유 있음)
- 재요청 방지 = cache 로 커버

### Dedup 전략
- **1차 (Cache)**: link 기준, TTL 내 재요청 skip
- **2차 (DB)**: link unique constraint, race condition 방지

---

## 구현 상태

1. → **Spec** (현재 문서)
2. → **Spike** (필요 시): DB 라이브러리, Scheduler 선택
3. → **Plan** 작성
4. → **Issue** 생성 (Epic)
5. → **Implementation** (TDD)

---

## 참고

- 이전 slice: [spec-news-fetch.md](spec-news-fetch.md) — GET /news endpoint
- TheNewsAPI 학습: `spikes/news_spikes/LEARNINGS.md`
- 원칙: [modular-monolith.md](architecture/modular-monolith.md), [xp.md](../../docs/architecture/principles/xp.md)
