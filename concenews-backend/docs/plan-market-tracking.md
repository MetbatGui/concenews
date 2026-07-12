# Plan: 마켓 추적 기능

> 설계 (Spec 기반: [spec-market-tracking.md](spec-market-tracking.md))
> Hexagonal + Modular Monolith 준수, shared_kernel/db 도입 (기존)

---

## 아키텍처

### 계층 구조 (market 모듈 신규)

```
Presentation (향후)
   ↓ (GET /markets 미구현 — Phase 2+)
Application
   └─ MarketCollectorService.run() (신규)
        ├─ PolymarketGammaAPIClient (외부 API adapter, port)
        ├─ MarketFilterPort → MacroMarketFilter (태그+키워드)
        └─ MarketRepositoryPort → PgMarketSnapshotRepository (persist)
   ↓
Infrastructure
   ├─ PolymarketGammaAPIClient (HTTP adapter, Gamma API)
   ├─ MacroMarketFilter (tag + keyword logic)
   ├─ PgMarketSnapshotRepository (SQLAlchemy)
   └─ SchedulerAdapter (scheduler registration)

Shared Kernel
   └─ db/
      ├─ engine.py (기존, SQLAlchemy engine)
      └─ base.py (기존, declarative base for ORM models)
```

### 데이터 흐름 (Collector)

```
Scheduler tick (5분)
   ↓
MarketCollectorService.run()
   ↓
PolymarketGammaAPIClient.fetch_markets(limit=100)
   ↓
For each market:
   ├─ Adapter: raw dict → Market (정규화)
   ├─ MarketFilterPort.is_macro(market)?
   │   ├─ No → skip
   │   └─ Yes → 계속
   ├─ Dedup: market_id + timestamp 조회, 가격 비교
   │   ├─ 동일 → skip (의미 있는 변화 없음)
   │   └─ 변경 → 계속
   └─ MarketRepositoryPort.save(snapshot)
        └─ Success → continue
```

### GET /markets 흐름 (향후)

```
GET /markets → MarketService.fetch_markets(filters) → Repository.find_recent() → response
```

Phase 2 이후 구현. 현재는 collector 만.

---

## Ports (Application)

```python
# application/ports.py

class MarketSourcePort(Protocol):
    """마켓 데이터 소스 (Gamma API)."""
    def fetch_markets(self, limit: int) -> list[dict]: ...


class MarketFilterPort(Protocol):
    """매크로 vs 노이즈 분류."""
    def is_macro(self, market: Market) -> bool: ...


class MarketRepositoryPort(Protocol):
    """마켓 스냅샷 저장소."""
    def save(self, snapshot: MarketSnapshot) -> MarketSnapshot: ...
    def find_recent(self, market_id: str, limit: int = 1) -> list[MarketSnapshot]: ...
    def find_all(self, limit: int = 100) -> list[MarketSnapshot]: ...


class SchedulerPort(Protocol):
    """백그라운드 스케줄러 (기존, news 모듈에서 도입)."""
    def schedule(self, func: Callable, interval_seconds: int) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
```

---

## Infrastructure (Adapters)

### Shared kernel: DB (기존)

- SQLAlchemy 2.0 sync + psycopg + Alembic
- 결정근거: [ADR 2026-07-06 db-library](../../docs/decisions/2026-07-06-db-library.md)

### market 모듈

- `infrastructure/polymarket_client.py` — PolymarketGammaAPIClient (HTTP adapter)
- `infrastructure/market_filter.py` — MacroMarketFilter (tag + keyword logic)
- `infrastructure/repositories.py` — PgMarketSnapshotRepository (신규)
- `application/services.py` — MarketCollectorService.run() (신규)

---

## DB Schema (PostgreSQL)

```sql
CREATE TABLE market_snapshot (
    id UUID PRIMARY KEY,                    -- Domain UUID v7
    market_id TEXT NOT NULL,                -- Polymarket ID (식별)
    question TEXT NOT NULL,
    outcomes TEXT[] NOT NULL,               -- ["Yes", "No"]
    outcome_prices FLOAT8[] NOT NULL,       -- [0.0585, 0.9415]
    last_price FLOAT8,
    best_bid FLOAT8,
    best_ask FLOAT8,
    spread FLOAT8,
    liquidity FLOAT8,
    volume_24h FLOAT8,
    volume_1w FLOAT8,
    volume_1m FLOAT8,
    end_date TIMESTAMPTZ NOT NULL,          -- KST aware
    active BOOLEAN DEFAULT true,
    closed BOOLEAN DEFAULT false,
    timestamp TIMESTAMPTZ NOT NULL,         -- 수집 시각 (KST)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_market_snapshot_market_id ON market_snapshot(market_id);
CREATE INDEX idx_market_snapshot_timestamp ON market_snapshot(timestamp DESC);
CREATE INDEX idx_market_snapshot_market_time ON market_snapshot(market_id, timestamp DESC);
```

---

## TDD 순서 & PR 구성

**원칙**: 각 PR = TDD cycle 완결 (RED + GREEN + Refactor). Merge 시 master green.

### 인프라 우선 (DB)

#### PR #1: Market Snapshot 테이블 — `feature/market-db-migration`

- Alembic migration: `market_snapshot` 테이블
- Unit test (schema 검증은 skip, alembic apply 확인만)
- 상태: **GREEN**

### market 모듈 확장

#### PR #2: Domain Model — `feature/market-domain-model`

- `domain/models.py` — Market, MarketSnapshot (Pydantic)
- Unit test (필드 검증, timezone 정규화)
- 상태: **GREEN**

#### PR #3: Market Filter — `feature/market-filter`

- `application/ports.py` 에 `MarketFilterPort` Protocol 추가
- `infrastructure/market_filter.py` — MacroMarketFilter (tag + keyword)
- Unit test (MACRO_TAG_IDS, MACRO_KEYWORDS 검증)
- 상태: **GREEN**

#### PR #4: Polymarket API Adapter — `feature/market-polymarket-adapter`

- `infrastructure/polymarket_client.py` — PolymarketGammaAPIClient
- Raw dict → Market 변환 (UTC → KST 정규화)
- Unit test (mock HTTP response)
- 상태: **GREEN**

#### PR #5: Repository — `feature/market-pg-repository`

- `infrastructure/repositories.py` — PgMarketSnapshotRepository
- Dedup 로직: market_id + timestamp 조회, 가격 비교
- Integration test: 실 PG (docker-compose), transaction rollback
- 파일: `tests/integration/market/test_market_repository_postgres.py`
- 상태: **GREEN**

#### PR #6: Collector Service — `feature/market-collector-service`

- `application/services.py` — MarketCollectorService.run()
- Filter → Repository 통합 흐름
- Unit test (Fake Filter + Fake Repository + Fake API Client)
- 상태: **GREEN**

#### PR #7: Wire up + Scheduler 등록 — `feature/market-collection-wire`

- Bootstrap 확장: PgMarketSnapshotRepository DI
- Scheduler 등록 (5분 주기, app startup 이벤트)
- Integration test (end-to-end: scheduler tick → API mock → DB 저장)
- `Closes #{issue}`
- 상태: **GREEN** (Phase 1 slice 완료)

---

## 폴더 구조 (변경 후)

```
concenews-backend/
├─ alembic/                       (기존)
│  ├─ env.py
│  └─ versions/
│     └─ {timestamp}_market_snapshot_table.py (신규)
├─ src/
│  ├─ shared_kernel/              (기존)
│  │  ├─ db/
│  │  │  ├─ engine.py
│  │  │  ├─ session.py
│  │  │  └─ base.py
│  ├─ modules/
│  │  ├─ news/                    (기존)
│  │  └─ market/                  (신규)
│  │     ├─ domain/
│  │     │  └─ models.py          (Market, MarketSnapshot)
│  │     ├─ application/
│  │     │  ├─ ports.py           (MarketSourcePort, MarketFilterPort, etc.)
│  │     │  ├─ services.py        (MarketCollectorService)
│  │     │  └─ handlers.py        (향후, GET /markets endpoint)
│  │     ├─ infrastructure/
│  │     │  ├─ polymarket_client.py   (PolymarketGammaAPIClient)
│  │     │  ├─ market_filter.py       (MacroMarketFilter)
│  │     │  └─ repositories.py    (PgMarketSnapshotRepository)
│  │     ├─ presentation/         (향후)
│  │     ├─ public.py             (향후)
│  │     └─ bootstrap.py          (DI 조립)
├─ tests/
│  ├─ integration/
│  │  └─ market/
│  │     ├─ test_market_repository_postgres.py
│  │     └─ test_market_collector_e2e.py
│  └─ unit/
│     ├─ market/
│     │  ├─ test_market_domain.py
│     │  ├─ test_market_filter.py
│     │  ├─ test_polymarket_adapter.py
│     │  └─ test_market_collector_service.py
```

---

## 의존성 예상

- **SQLAlchemy 2.0** (기존, DB)
- **Alembic** (기존, migration)
- **psycopg** (기존, PG driver)
- **httpx** or **requests** (Polymarket API HTTP client)
- **pydantic** (기존, domain model)

---

## 알려진 Unknowns → Spike 대상 (on-demand)

| Spike          | Trigger 시점                | 학습 대상                                 | 상태 |
| -------------- | --------------------------- | ----------------------------------------- | ---- |
| API rate limit | Collector 첫 배포 후        | 실측 호출량, 응답 시간, 에러율 모니터링  | 대기 |
| Tag 추가 발견  | 월 1-2회 spike 실행         | 신규 매크로 태그 분류, ADR 갱신           | 대기 |

---

## 향후 확장

### Phase 2: Spike Detection
- CLOB API: `GET /price-history` 추가
- MarketSpike 테이블 (가격 변화 기록)
- Spike detection 로직 (10%+ threshold)
- 상세: [ADR 2026-07-12 polymarket-api-choice](../../docs/decisions/2026-07-12-polymarket-api-choice.md) (Phase 2 섹션)

### Phase 3: Trader Tracking
- Data API: `GET /holders?market=...` 호출
- TraderSnapshot 테이블
- Credibility scoring (account age, win rate, volume)

### Phase 3+: News-Market-Trader Matching
- News spike 감지 → market spike + trader positions 확인
- Anomaly alert (역배 위험 신호)

---

**버전**: 1.0  
**작성일**: 2026-07-12  
**상태**: 설계 완료 (TDD 구현 시작 대기)
