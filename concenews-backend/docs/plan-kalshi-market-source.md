# Plan: Kalshi 마켓 데이터 소스 전환 (Domain 재설계 + Walking Skeleton)

**버전**: 1.0
**작성일**: 2026-09-17
**Spec**: [spec-kalshi-market-source.md](spec-kalshi-market-source.md) v1.0(Proposed)

---

## 범위 요약

**포함**:
- Domain 재설계: `MarketMetadata`, `Category`(구 `Tag`), `MarketClassification`, `classify()` 시그니처를 Kalshi 구조로 변경
- `MarketSourcePort` 재설계: `order`/`ascending` 제거, `fetch_tags_bulk` → `fetch_categories_bulk`
- `KalshiMarketClient` Walking Skeleton (하드코딩 스텁)
- 기존 `PolymarketGammaClient`·프로덕션 기본 배선은 변경하지 않음 — `bootstrap()`에 `source` 주입 지점이 이미 있으므로 그걸로 스텁을 검증만 한다

**제외 (후속 Slice)**:
- `KalshiMarketClient`의 실제 HTTP 구현
- 프로덕션 기본 소스를 Kalshi로 전환(bootstrap 기본값 변경)
- 실제 MACRO/NON_MACRO 카테고리 목록 확정
- `market-participant` 모듈 재설계
- "주요 마켓" 클라이언트 사이드 랭킹

---

## 아키텍처 (변경 후)

```
Application
   └─ MarketClassifierService.run()   (변경 없음, 흐름 그대로)
        ├─ MarketSourcePort  → KalshiMarketClient (신규, 스텁) | PolymarketGammaClient (기존, 유지)
        └─ ClassificationRepositoryPort → PgMarketClassificationRepository (변경 없음)

Domain (재설계)
   ├─ MarketMetadata  (market_id, series_id, question, end_date)
   ├─ Category        (id: str)                      ← Tag(id: int, label, slug) 대체
   ├─ Classification  (enum, 변경 없음)
   ├─ MarketClassification (market_id, question, classification, categories: tuple[str, ...], end_date, classified_at)
   └─ classify(category_ids: set[str]) → Classification | None   (시그니처 변경, blacklist/whitelist 값은 placeholder)

Infrastructure (추가, 기존 유지)
   ├─ KalshiMarketClient      (신규, 스텁 — MarketSourcePort 구현)
   ├─ PolymarketGammaClient   (기존, 유지 — 제거하지 않음, 프로덕션 기본값)
   └─ PgMarketClassificationRepository (변경 없음)
```

---

## 데이터 흐름 (스텁 기준)

```
Integration test
   ↓
MarketClassifierService(source=KalshiMarketClient(stub), repository=...)
   ↓
1. repo.find_active_condition_ids(now)  →  cached_ids: set[str]        (변경 없음)
   ↓
2. source.fetch_active_markets(limit=500)  →  markets: list[MarketMetadata]   (order/ascending 제거)
   ↓
3. new_ids = [m.market_id for m in markets if m.market_id not in cached_ids]
   ↓
4. category_map = await source.fetch_categories_bulk(series_ids_of(new_markets))  →  dict[str, str]
   (series_id → 주 카테고리. 스텁 단계에선 하드코딩 값 반환)
   ↓
5. for each new market:
     result = classify({category_map[m.series_id]})
     if result in {MACRO, NON_MACRO}:
       classifications.append(MarketClassification(...))
   ↓
6. repo.save_bulk(classifications)   (변경 없음)
```

`docs/research/kalshi-api-contract.md`에서 확인한 실제 Series→Event→Market 2단계 조회는 **실제 HTTP 구현 PR(후속 Slice)** 에서 반영한다. 이 Slice의 `KalshiMarketClient`는 하드코딩 응답만 반환하는 스텁이라 실제 조인 로직이 없다.

---

## Ports (변경)

```python
# application/ports.py

class MarketSourcePort(Protocol):
    async def fetch_active_markets(self, limit: int) -> list[MarketMetadata]: ...
    #   ↑ order, ascending 파라미터 제거 (Kalshi 서버 사이드 정렬 없음)

    async def fetch_categories_bulk(
        self, series_ids: list[str]
    ) -> dict[str, str]: ...
    #   ↑ fetch_tags_bulk(condition_ids) -> dict[str, list[Tag]] 대체
    #     series_id → 주 카테고리 문자열 매핑 (Kalshi: category는 Series/Event 레벨)
```

`ClassificationRepositoryPort`는 변경 없음 — `find_active_condition_ids`/`save_bulk` 시그니처는 Domain 필드명이 바뀌어도 타입(`str`, `list[MarketClassification]`)이 동일해 그대로 재사용한다.

---

## Domain (변경)

```python
# domain/models.py

class Category(BaseModel, frozen=True):
    id: str  # Kalshi 카테고리 문자열, 예: "Economics" (정수 ID 아님 — Tag와 다름)


class MarketMetadata(BaseModel, frozen=True):
    market_id: str    # Kalshi ticker (구 condition_id)
    series_id: str    # Kalshi series_ticker (카테고리 조인 키)
    question: str
    end_date: datetime


class MarketClassification(BaseModel, frozen=True):
    market_id: str
    question: str
    classification: Classification
    categories: tuple[str, ...]   # 구 tags: tuple[Tag, ...]
    end_date: datetime
    classified_at: datetime


# domain/classifier.py

NON_MACRO_CATEGORIES: frozenset[str] = frozenset()  # placeholder — 실제 값은 후속 조사
MACRO_CATEGORIES: frozenset[str] = frozenset()      # placeholder

def classify(categories: set[str]) -> Classification | None:
    """Blacklist 우선. None = UNKNOWN (제외). placeholder 상수라 실제로는 전부 None."""
    if categories & NON_MACRO_CATEGORIES:
        return Classification.NON_MACRO
    if categories & MACRO_CATEGORIES:
        return Classification.MACRO
    return None
```

**주의**: `NON_MACRO_CATEGORIES`/`MACRO_CATEGORIES`가 빈 집합이므로 이 Slice가 끝나도 `classify()`는 실질적으로 전부 `None`(UNKNOWN)을 반환한다 — Spec의 명시적 제외 사항이며, 다음 Slice에서 실제 카테고리 조사 후 채운다. Unit test는 "빈 상수 상태에서 항상 None"을 검증한다(임시 계약이지만 명시적으로 테스트해야 나중에 실수로 깨지지 않는다).

---

## Walking Skeleton — `KalshiMarketClient` 스텁

```python
# infrastructure/kalshi_client.py

class KalshiMarketClient:
    """Kalshi MarketSourcePort 구현 — Walking Skeleton 스텁.

    하드코딩 응답만 반환한다. 실제 HTTP 호출은 후속 PR.
    """

    async def fetch_active_markets(self, limit: int) -> list[MarketMetadata]:
        return []  # 스텁: 빈 리스트 (Integration test가 실제 검증은 fixture로)

    async def fetch_categories_bulk(self, series_ids: list[str]) -> dict[str, str]:
        return {}
```

Integration test는 이 스텁에 `MagicMock`이 아니라 **하드코딩된 값을 반환하는 별도 Fake**(`FakeKalshiSource`, `tests/integration/market/data.py` 패턴)를 주입해 실제로 데이터가 흐르는지 검증한다 — 빈 리스트만 반환하는 프로덕션 스텁 자체를 검증 대상으로 삼지 않는다(xp.md Classicist 원칙).

---

## PR 순서 (TDD, 3 PR)

**원칙**: 각 PR = RED → GREEN → Refactor 완결. Merge 시 master green.

### PR #1: Walking Skeleton — `feature/kalshi-market-source-acceptance`

- Integration test 신설: `tests/integration/market/test_kalshi_classifier_integration.py`
  - `FakeKalshiSource`(하드코딩 마켓 2-3개 + 카테고리 매핑)를 `MarketClassifierService`에 주입
  - `run()` 호출 → 새 Domain 필드(`market_id`, `categories`)로 DB에 저장되는지 확인
  - `classify()`가 placeholder 상수로 전부 `None`을 반환하므로, 이 시점 assertion은 "저장 흐름 자체가 안 끊긴다"(빈 저장 포함)를 증명하는 데 집중한다
- `KalshiMarketClient` 스텁 파일 생성(위 코드)
- Domain·Port는 이 PR에서 최소 골격만(다음 PR에서 완성) — Walking Skeleton 관례상 모든 계층을 우선 잇는다

### PR #2: Domain 재설계 — `feature/kalshi-market-source-domain`

- `domain/models.py`: `Tag` 제거, `Category` 신설, `MarketMetadata`/`MarketClassification` 필드 교체
- `domain/classifier.py`: `classify()` 시그니처를 `set[str]`로 변경, `NON_MACRO_CATEGORIES`/`MACRO_CATEGORIES`(빈 placeholder)로 교체
- Unit test 갱신: `tests/unit/market/test_classifier.py`, `test_market_domain.py` — 새 필드명 반영 + "빈 상수 → 항상 None" 케이스
- **주의**: 기존 `PolymarketGammaClient`가 `Tag`/`MarketMetadata`를 그대로 참조하므로, 이 PR에서 Polymarket 어댑터도 새 Domain 타입에 맞게 함께 고쳐야 컴파일이 깨지지 않는다(Polymarket 어댑터 자체의 동작 변경은 아니고 타입 어댑팅만) — 기존 태그 응답을 `Category(id=str(tag.id))` 식으로 감싸는 얇은 변환.

### PR #3: Port 재정의 + Service 연결 — `feature/kalshi-market-source-port`

- `application/ports.py`: `MarketSourcePort` 시그니처 변경(`fetch_active_markets(limit)`, `fetch_categories_bulk`)
- `application/services.py`: `MarketClassifierService.run()`이 새 시그니처로 호출하도록 조정(흐름 구조는 동일, 호출부만)
- `KalshiMarketClient` 스텁이 새 Port를 구현하도록 최종 정리
- PR #1의 Integration test가 이 시점부터 실질적인 스텁 계약(빈 리스트가 아니라 Fake 데이터)까지 통과하는지 재확인
- `bootstrap.py`는 변경하지 않는다(프로덕션 기본값은 여전히 `PolymarketGammaClient`) — Kalshi 전환은 실제 HTTP 구현이 끝나는 후속 Slice에서.

---

## 폴더 구조 (이 Slice 완료 시)

```
concenews-backend/
├─ src/modules/market/
│  ├─ domain/
│  │  ├─ models.py                (Category, MarketMetadata, MarketClassification 재정의)
│  │  └─ classifier.py            (classify(set[str]), placeholder 상수)
│  ├─ application/
│  │  ├─ ports.py                 (MarketSourcePort 재정의)
│  │  └─ services.py              (호출부만 조정)
│  └─ infrastructure/
│     ├─ polymarket_client.py     (기존 유지, 타입만 어댑팅)
│     └─ kalshi_client.py         (신규, 스텁)
└─ tests/
   ├─ unit/market/
   │  ├─ test_classifier.py           (갱신)
   │  └─ test_market_domain.py        (갱신)
   └─ integration/market/
      ├─ data.py                       (FakeKalshiSource 데이터 추가)
      └─ test_kalshi_classifier_integration.py   (신규)
```

---

## 의존성 변경

없음 — 이 Slice는 스텁만 다루므로 신규 HTTP 라이브러리 불필요. `httpx` 도입은 실제 HTTP 구현 Slice에서.

---

## Slice 완료 조건 (Definition of Done)

- [ ] PR #1-#3 모두 merge, master green
- [ ] `Tag`/`condition_id`/`Polymarket` 문자열이 신규 Domain·Port 코드에 없음
- [ ] `PolymarketGammaClient` 및 프로덕션 `bootstrap()` 기본값은 변경되지 않음(회귀 없음)
- [ ] Integration test: `FakeKalshiSource` 기반 흐름이 GREEN
- [ ] 로컬 품질 게이트(`just check-branch-green`) green

## 후속 Slice (참고)

- Kalshi 실제 HTTP 구현 (Series→Event→Market 2단계 조회, `docs/research/kalshi-api-contract.md` 반영)
- MACRO/NON_MACRO 카테고리 목록 확정
- 프로덕션 기본 소스 Kalshi 전환(`bootstrap()` 기본값 변경)
- `market-participant` 모듈 — 체결 규모 감지로 재정의
