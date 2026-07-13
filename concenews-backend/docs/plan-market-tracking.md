# Plan: Slice A — 매크로 마켓 분류

**버전**: 2.0
**작성일**: 2026-07-13
**Spec**: [spec-market-tracking.md](spec-market-tracking.md) v3.0

---

## 범위 요약

**포함 (Slice A)**:
- Polymarket 활성 마켓 fetch (volume24hr 상위 500)
- 태그 기반 분류 (MACRO / NON_MACRO)
- `market_classification` 테이블 저장 + end_date 캐싱
- 5분 주기 스케줄러

**제외 (Slice B 이후)**:
- 가격 스냅샷 / 히스토리
- 스파이크 감지
- GET /markets 조회 endpoint
- 트레이더 추적

---

## 아키텍처 (Hexagonal + Modular Monolith)

```
Application
   └─ MarketClassifierService.run()
        ├─ MarketSourcePort  → PolymarketGammaClient (async)
        ├─ TagSourcePort     → PolymarketGammaClient (async, 병렬)
        └─ ClassificationRepositoryPort → PgMarketClassificationRepository

Domain
   ├─ MarketMetadata  (id, question, end_date)
   ├─ Tag             (id, label, slug)
   ├─ Classification  (enum: MACRO, NON_MACRO)
   ├─ MarketClassification (aggregate)
   └─ classify(tag_ids) → Classification | None   (pure function)

Infrastructure
   ├─ PolymarketGammaClient  (httpx.AsyncClient)
   ├─ PgMarketClassificationRepository (SQLAlchemy 2.0)
   └─ SchedulerAdapter (기존, news 모듈에서 도입)

Shared Kernel
   └─ db/ (기존)
```

---

## 데이터 흐름

```
Scheduler tick (5분)
   ↓
MarketClassifierService.run()
   ↓
1. repo.find_active_condition_ids(now)  →  cached_ids: set[str]
   ↓
2. source.fetch_active_markets(limit=500, order='volume24hr')  →  markets: list[MarketMetadata]
   ↓
3. new_ids = [m.id for m in markets if m.id not in cached_ids]
   ↓
4. tag_map = await source.fetch_tags_bulk(new_ids)  →  dict[str, list[Tag]]  (asyncio.gather)
   ↓
5. for each new market:
     result = classify(tag_ids_of(market))
     if result in {MACRO, NON_MACRO}:
       classifications.append(MarketClassification(...))
     # UNKNOWN → skip
   ↓
6. repo.save_bulk(classifications)
```

---

## Ports

```python
# application/ports.py

class MarketSourcePort(Protocol):
    async def fetch_active_markets(
        self, limit: int, order: str, ascending: bool
    ) -> list[MarketMetadata]: ...

    async def fetch_tags_bulk(
        self, condition_ids: list[str]
    ) -> dict[str, list[Tag]]: ...


class ClassificationRepositoryPort(Protocol):
    def find_active_condition_ids(self, now: datetime) -> set[str]: ...
    def save_bulk(self, classifications: list[MarketClassification]) -> None: ...
```

---

## Domain

```python
# domain/models.py

class Classification(str, Enum):
    MACRO = "MACRO"
    NON_MACRO = "NON_MACRO"


class Tag(BaseModel, frozen=True):
    id: int
    label: str
    slug: str


class MarketMetadata(BaseModel, frozen=True):
    condition_id: str
    question: str
    end_date: datetime


class MarketClassification(BaseModel, frozen=True):
    condition_id: str
    question: str
    classification: Classification
    tags: tuple[Tag, ...]
    end_date: datetime
    classified_at: datetime


# domain/classifier.py

NON_MACRO_IDS: frozenset[int] = frozenset({1, 100350, 102232, ...})
MACRO_IDS: frozenset[int] = frozenset({120, 100328, 159, ...})

def classify(tag_ids: set[int]) -> Classification | None:
    """Blacklist 우선. None = UNKNOWN (제외)."""
    if tag_ids & NON_MACRO_IDS:
        return Classification.NON_MACRO
    if tag_ids & MACRO_IDS:
        return Classification.MACRO
    return None
```

---

## DB Schema

```sql
CREATE TABLE market_classification (
    condition_id   TEXT PRIMARY KEY,
    question       TEXT NOT NULL,
    classification TEXT NOT NULL,   -- 'MACRO' | 'NON_MACRO'
    tags_json      JSONB NOT NULL,
    end_date       TIMESTAMPTZ NOT NULL,
    classified_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_market_classification_end_date
    ON market_classification(end_date);

CREATE INDEX idx_market_classification_type
    ON market_classification(classification);
```

기존 `market_snapshot` 테이블 → Slice B 에서 재사용 (지금은 그대로 둠).

---

## PR 순서 (TDD, 6 PR)

**원칙**: 각 PR = RED → GREEN → Refactor 완결. Merge 시 master green.
**패턴**: Walking Skeleton 1 PR (acceptance test + stub = GREEN 통합, `xp.md` § "PR 분할 시 주의" 준수). 이후 각 PR 이 스텁 교체.

### PR #1: Walking Skeleton — `feature/market-classification-acceptance`

- Migration `market_classification` 테이블 (실제 스키마, E2E 테스트에 필요)
- E2E acceptance integration test 작성 (`tests/integration/market/test_classifier_e2e.py`)
  - Fake HTTP 응답 → Service.run() → DB에 분류 저장 확인
- 최소 스텁 구현으로 GREEN:
  - `MarketClassifierService.run()` — pass (또는 no-op)
  - `PolymarketGammaClient` — 하드코딩 응답
  - `PgMarketClassificationRepository` — save/find 최소 구현 (실제 SQL은 PR #3)
  - `bootstrap.py` — DI 뼈대
- 각 PR 이 스텁을 실제로 교체하는 기반.

### PR #2: Domain — `feature/market-domain-classifier`

- `domain/models.py` — Classification enum, Tag, MarketMetadata, MarketClassification (frozen Pydantic)
- `domain/classifier.py` — `classify()` pure function + NON_MACRO_IDS / MACRO_IDS 상수
- Unit test:
  - blacklist 히트 → NON_MACRO
  - whitelist 히트 → MACRO
  - blacklist+whitelist 동시 → NON_MACRO 우선
  - 둘 다 없음 → None
- 파일: `tests/unit/market/test_classifier.py`, `tests/unit/market/test_market_domain.py`

### PR #3: Repository 실제 구현 — `feature/market-classification-repository`

- `infrastructure/repositories.py` — PR #1 스텁을 실제 SQL로 교체
  - `find_active_condition_ids(now)`: SELECT WHERE end_date > NOW()
  - `save_bulk(list)`: INSERT ON CONFLICT DO NOTHING
- Integration test: 실 PG (docker-compose)
- 파일: `tests/integration/market/test_classification_repository.py`
- Migration은 PR #1 에서 이미 완료.

### PR #4: Polymarket Async Adapter 실제 구현 — `feature/market-polymarket-adapter`

- `infrastructure/polymarket_client.py` — PR #1 하드코딩 응답을 httpx.AsyncClient 로 교체
  - `fetch_active_markets`: `GET /markets` × 5 페이지 (volume24hr desc, active=true)
  - `fetch_tags_bulk`: `asyncio.gather` 로 병렬 `GET /markets/{id}/tags`
- Unit test: `httpx.MockTransport` 로 응답 mock, 페이지네이션 + 병렬 검증
- 파일: `tests/unit/market/test_polymarket_adapter.py`
- 의존성: `httpx` prod 추가, `aiohttp` / `httpx2` dev 제거

### PR #5: Classifier Service 실제 흐름 — `feature/market-classifier-service`

- `application/services.py` — PR #1 스텁을 실제 흐름으로 교체
  - Repository 캐시 조회 → 신규 fetch → 태그 병렬 조회 → classify → save
- Unit test: Fake source + Fake repo, UNKNOWN skip 검증
- 파일: `tests/unit/market/test_classifier_service.py`

### PR #6: Scheduler 등록 완성 — `feature/market-classifier-wire`

- `bootstrap.py`: FastAPI lifespan 에 5분 주기 스케줄러 등록 (PR #1 뼈대에 실제 등록 추가)
- E2E test 확장 (스케줄러 tick 검증)
- `Closes #23`

---

## 폴더 구조 (Slice A 완료 시)

```
concenews-backend/
├─ alembic/versions/
│  ├─ 3e9fcf0f6d4e_market_snapshot_table.py  (기존, Slice B 용)
│  └─ {new}_market_classification_table.py   (PR #1)
├─ src/modules/market/
│  ├─ domain/
│  │  ├─ models.py                (Classification, Tag, MarketMetadata, MarketClassification)
│  │  └─ classifier.py            (classify() + TAG_IDS)
│  ├─ application/
│  │  ├─ ports.py                 (MarketSourcePort, ClassificationRepositoryPort)
│  │  └─ services.py              (MarketClassifierService)
│  ├─ infrastructure/
│  │  ├─ polymarket_client.py     (async Gamma adapter)
│  │  └─ repositories.py          (PgMarketClassificationRepository)
│  └─ bootstrap.py                (DI 조립)
└─ tests/
   ├─ unit/market/
   │  ├─ test_classifier.py
   │  ├─ test_polymarket_adapter.py
   │  └─ test_classifier_service.py
   └─ integration/market/
      ├─ test_market_classification_migration.py
      ├─ test_classification_repository.py
      └─ test_classifier_e2e.py
```

---

## 의존성 변경

**추가 (prod)**:
- `httpx` — async HTTP 클라이언트. sync/async 통합 API, FastAPI 생태계 표준.

**제거 (dev)**:
- `aiohttp` — 스파이크용으로 임시 추가됨. httpx로 대체.
- `httpx2` — 오타로 추정 (`httpx` 오타). 정리.

**대체 검토 (prod)**:
- `requests` — 뉴스 모듈 등에서 사용 중이면 유지. 신규 코드는 httpx 사용.
  (완전 통합은 별도 refactor slice 로 미룸.)

**기존 유지**:
- SQLAlchemy 2.0, Alembic, psycopg, pydantic

---

## Slice 완료 조건 (Definition of Done)

- [ ] PR #1-#6 모두 merge, master green
- [ ] Integration test (E2E): 스케줄러 실행 → DB에 MACRO/NON_MACRO 저장 확인
- [ ] 로컬 실측: 실제 Gamma API 대상 실행 → 500 마켓 분류 완료 확인 (10초 이내)
- [ ] LEARNINGS 참조 링크 유효

---

## Slice B 이후 (참고)

- Slice B: 스냅샷 수집 + 급변 감지 (별도 spec/plan)
- Slice C: 트레이더 추적 (Data API 스파이크 선행)
- Slice D: 뉴스-마켓 매칭 (News BC 연동)
