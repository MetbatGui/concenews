# Plan: 뉴스 수집 기능

> 설계 (Spec 기반: [spec-news-collection.md](spec-news-collection.md))
> Hexagonal + Modular Monolith 준수, shared_kernel/db 도입

---

## 아키텍처

### 계층 구조 (news 모듈 확장)

```
Presentation (기존)
   ↓ (변경 없음, GET /news)
Application
   ├─ NewsService.fetch_news() (기존, Repository 교체 예정)
   └─ NewsCollectorService.run() (신규)
        ├─ TheNewsAPIClient (외부 API adapter, port)
        ├─ CachePort → InMemoryCacheAdapter (dedup 1차)
        └─ NewsRepositoryPort → PgNewsRepository (dedup 2차 + persist)
   ↓
Infrastructure
   ├─ TheNewsAPIClient (외부 HTTP)
   ├─ InMemoryCacheAdapter (dict + TTL)
   ├─ PgNewsRepository (SQLAlchemy)
   └─ SchedulerAdapter (APScheduler wrapper)

Shared Kernel (신규)
   └─ db/
      ├─ engine.py (SQLAlchemy engine + session factory)
      └─ base.py (declarative base for ORM models)
```

### 데이터 흐름 (Collector)

```
Scheduler tick (15분)
   ↓
NewsCollectorService.run()
   ↓
TheNewsAPIClient.fetch(keywords=["interest rate", "forex", ...])
   ↓
For each raw item:
   ├─ Adapter: raw dict → NewsItem (KST 변환 포함)
   ├─ CachePort.contains(item.link)?
   │   ├─ Yes → skip
   │   └─ No → 계속
   ├─ NewsRepositoryPort.save(item)
   │   ├─ Success → CachePort.set(item.link, TTL=15min)
   │   └─ Conflict (unique link) → skip
```

### GET /news 흐름 (변경 없음)

```
GET /news → NewsService.fetch_news(limit) → NewsRepository.find_all() → response
```

Repository 는 `InMemoryNewsRepository` → `PgNewsRepository` 로 교체 (Bootstrap 조립 변경).

---

## Ports (Application)

```python
# application/ports.py — 기존 IdGenerator 옆에 추가

class CachePort(Protocol):
    """재요청 방지 캐시 (link → sentinel)."""
    def contains(self, key: str) -> bool: ...
    def set(self, key: str, ttl_seconds: int) -> None: ...


class NewsRepositoryPort(Protocol):
    """뉴스 영구 저장소."""
    def save(self, item: NewsItem) -> NewsItem: ...
    def find_all(self, limit: int) -> list[NewsItem]: ...


class NewsSourcePort(Protocol):
    """뉴스 소스 (외부 뉴스가 오는 곳). Adapter: TheNewsAPI 등."""
    def fetch(self, keywords: list[str]) -> list[dict]: ...


class SchedulerPort(Protocol):
    """백그라운드 스케줄러."""
    def schedule(self, func: Callable, interval_seconds: int) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
```

---

## Infrastructure (Adapters)

### Shared kernel: DB

- **Library**: SQLAlchemy 2.0 sync + psycopg + Alembic
- **결정 근거**: [ADR 2026-07-06 db-library](../../docs/decisions/2026-07-06-db-library.md)
- `src/shared_kernel/db/engine.py` — SQLAlchemy engine (`create_engine`), Session factory
- `src/shared_kernel/db/base.py` — Declarative base (`DeclarativeBase`)
- `src/shared_kernel/db/session.py` — Session provider (context manager)
- Alembic migration (`alembic/versions/`)
- DSN: 환경 변수 `DATABASE_URL` (기본: `postgresql+psycopg://concenews:concenews@localhost:5432/concenews`)

### news 모듈

- `infrastructure/repositories.py` — `InMemoryNewsRepository` (기존) + `PgNewsRepository` (신규)
- `infrastructure/cache.py` — `InMemoryCacheAdapter` (dict + timestamp)
- `infrastructure/the_news_api_client.py` — TheNewsAPI HTTP adapter
- `infrastructure/scheduler.py` — `ApSchedulerAdapter` (APScheduler wrapping)

---

## DB Schema (PostgreSQL)

```sql
CREATE TABLE news (
    id UUID PRIMARY KEY,                    -- Domain UUID v7
    title TEXT NOT NULL,
    description TEXT,
    link TEXT NOT NULL UNIQUE,              -- 2차 dedup key
    source TEXT NOT NULL,
    published_at TIMESTAMPTZ NOT NULL,      -- KST aware
    keywords TEXT DEFAULT '',
    categories TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_news_published_at ON news(published_at DESC);
```

---

## 알려진 Unknowns → Spike 대상 (on-demand)

Slice 진행 중 아래 시점에 spike:

| Spike          | Trigger 시점                | 학습 대상                                            | 상태 |
| -------------- | --------------------------- | ---------------------------------------------------- | ---- |
| DB 라이브러리  | Shared kernel DB 도입 직전  | SQLAlchemy 2.0 async vs sync, session 관리           | ✅ 완료 ([ADR](../../docs/decisions/2026-07-06-db-library.md), Sync psycopg 채택) |
| Scheduler 선택 | Scheduler adapter 구현 직전 | APScheduler vs FastAPI-scheduler vs 기타             | 대기 |
| Cache impl     | 필요 시                     | stdlib `dict + timestamp` 로 충분? 라이브러리 필요?  | 대기 |

각 spike 완료 시 ADR + 문서 갱신.

---

## TDD 순서 & PR 구성

**원칙**: 각 PR = TDD cycle 완결 (RED + GREEN + Refactor). Merge 시 master green.

### 인프라 우선 (shared kernel)

#### PR #1: DB Shared Kernel — `feature/shared-db-setup`

- **Spike 선행**: `spikes/db/` — SQLAlchemy async vs sync, alembic setup
- **ADR**: DB 선택 근거
- `src/shared_kernel/db/` — engine, session, base
- `alembic/` 초기화
- Unit test (session factory 동작)
- 상태: **GREEN**

#### PR #2: Scheduler Shared Kernel — `feature/shared-scheduler`

- **Spike 선행**: `spikes/scheduler/` — APScheduler 등 비교
- **ADR**: Scheduler 선택 근거
- `src/shared_kernel/scheduler/` — Port + Adapter (또는 news 모듈 로컬로 시작)
- Unit test
- 상태: **GREEN**

### news 모듈 확장

#### PR #3: PgNewsRepository — `feature/news-pg-repository`

- Alembic migration: `news` 테이블
- `PgNewsRepository` impl (Port 는 기존 InMemory 와 계약 통일)
- Unit test (transaction rollback fixture)
- Integration test (real PG via testcontainers or docker-compose)
- 상태: **GREEN**

#### PR #4: Cache Adapter — `feature/news-cache-adapter`

- `application/ports.py` 에 `CachePort` 추가
- `infrastructure/cache.py` — `InMemoryCacheAdapter` (dict + TTL)
- Unit test (TTL 동작, contains/set)
- 상태: **GREEN**

#### PR #5: TheNewsAPI Adapter — `feature/news-thenewsapi-adapter`

- `infrastructure/the_news_api_client.py`
- Raw dict → NewsItem 변환 (UTC → KST 정규화)
- Unit test (mock HTTP response)
- 상태: **GREEN**

#### PR #6: NewsCollectorService — `feature/news-collector-service`

- `application/services.py` 에 `NewsCollectorService.run()` 추가
- Cache → Repository → API 통합 흐름
- Unit test (Fake CachePort + FakeRepository + FakeAPIClient)
- 상태: **GREEN**

#### PR #7: Wire up + Scheduler 등록 — `feature/news-collection-wire`

- Bootstrap 확장: PgNewsRepository DI (InMemory 교체)
- Scheduler 등록 (앱 startup 이벤트)
- Integration test (end-to-end: scheduler tick → API mock → DB 저장)
- **GET /news** acceptance test 는 그대로 유지 (Repository 만 교체됨)
- `Closes #{issue}`
- 상태: **GREEN** (전체 slice 완료)

---

## 폴더 구조 (변경 후)

```
concenews-backend/
├─ alembic/                       (신규)
│  ├─ env.py
│  └─ versions/
├─ src/
│  ├─ shared_kernel/              (신규)
│  │  ├─ db/
│  │  │  ├─ engine.py
│  │  │  ├─ session.py
│  │  │  └─ base.py
│  │  └─ scheduler/               (선택 — Rule of Three, news 만이면 로컬)
│  ├─ modules/
│  │  └─ news/
│  │     ├─ domain/models.py      (기존)
│  │     ├─ application/
│  │     │  ├─ ports.py           (기존 + CachePort/RepoPort/APIClientPort)
│  │     │  └─ services.py        (기존 NewsService + NewsCollectorService)
│  │     ├─ infrastructure/
│  │     │  ├─ repositories.py    (기존 + PgNewsRepository)
│  │     │  ├─ id_generator.py    (기존)
│  │     │  ├─ cache.py           (신규)
│  │     │  ├─ the_news_api_client.py (신규)
│  │     │  └─ scheduler.py       (신규 — 또는 shared_kernel 로)
│  │     ├─ presentation/         (변경 없음)
│  │     ├─ public.py             (변경 없음, 또는 collector service export)
│  │     └─ bootstrap.py          (Repository DI 교체)
```

---

## 의존성 예상

- **SQLAlchemy 2.0** (DB, sync — ADR 2026-07-06 db-library)
- **Alembic** (migration)
- **psycopg** (PG driver)
- **APScheduler** (스케줄러 — spike 후 결정)
- **cachetools** or stdlib (cache — spike 후 결정)
- **httpx** or **requests** (TheNewsAPI HTTP client)

---

## 향후 확장

- Cache Redis 대체 (`RedisCacheAdapter` 구현, `CachePort` 인터페이스 유지)
- 다중 뉴스 소스 (RSS 등, `NewsSourcePort` 확장)
- 실시간 push (SSE/WebSocket)
- 사용자별 필터 (cross-slice)
