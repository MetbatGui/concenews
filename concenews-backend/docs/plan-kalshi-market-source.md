# Plan: Kalshi 마켓 데이터 소스 전환 (Domain 병존 추가 + Walking Skeleton)

**버전**: 2.0 (병존 추가 방식으로 재작성)
**작성일**: 2026-09-17
**Spec**: [spec-kalshi-market-source.md](spec-kalshi-market-source.md) v2.0(Proposed)

---

## 범위 요약

**포함**:
- 신규 Domain: `KalshiMarketMetadata` (기존 `MarketMetadata`/`Tag`와 별개; 카테고리는 `dict[str, str]`로 충분해 별도 타입 없음 — Independent Review에서 YAGNI로 제거)
- 신규 Port: `KalshiMarketSourcePort` (기존 `MarketSourcePort`와 별개)
- 신규 함수: `classify_by_category()` + `NON_MACRO_CATEGORIES`/`MACRO_CATEGORIES`(빈 placeholder) — 기존 `classify()`와 별개
- `KalshiMarketClient` Walking Skeleton (하드코딩 스텁)

**제외 (후속)**:
- `KalshiMarketClient`의 실제 HTTP 구현
- 실제 카테고리 매핑 확정 (별도 Task)
- Kalshi 결과를 저장하는 Service·Repository 배선 (실 HTTP 구현과 함께 결정)
- 기존 Polymarket 코드 — **전혀 변경 없음**
- `market-participant` 모듈 재설계

---

## 아키텍처

```
신규 (병존, 기존과 무관)
   KalshiMarketClient (스텁) → KalshiMarketSourcePort
        ├─ fetch_active_markets(limit) -> list[KalshiMarketMetadata]
        └─ fetch_categories_bulk(series_ids) -> dict[str, str]

   classify_by_category(categories: set[str]) -> Classification | None
        (NON_MACRO_CATEGORIES, MACRO_CATEGORIES = 빈 placeholder)

기존 (무변경)
   MarketClassifierService → MarketSourcePort → PolymarketGammaClient
   classify(tag_ids: set[int]) → Classification | None
        (NON_MACRO_IDS, MACRO_IDS = 기존 실측값 그대로)
```

두 흐름은 `domain/models.py`, `domain/classifier.py`, `application/ports.py` 파일을 공유하되 클래스/함수 단위로는 완전히 분리된다. 같은 파일 안에 신규 타입을 추가하는 것뿐, 기존 타입의 정의는 한 줄도 바뀌지 않는다.

---

## Domain (신규 추가분만)

```python
# domain/models.py 에 추가 (기존 클래스는 무변경)

class KalshiMarketMetadata(BaseModel):
    """Kalshi 마켓 메타데이터.

    임시: Polymarket 어댑터 제거 시 `MarketMetadata`로 리네임 예정.
    """

    model_config = ConfigDict(frozen=True)

    market_id: str    # Kalshi ticker
    series_id: str    # Kalshi series_ticker (카테고리 조인 키)
    question: str
    end_date: datetime
```

```python
# domain/classifier.py 에 추가 (기존 classify/NON_MACRO_IDS/MACRO_IDS는 무변경)

NON_MACRO_CATEGORIES: frozenset[str] = frozenset()  # placeholder — 실제 값은 별도 Task
MACRO_CATEGORIES: frozenset[str] = frozenset()      # placeholder

def classify_by_category(categories: set[str]) -> Classification | None:
    """카테고리 문자열 집합으로 마켓 분류 (Kalshi 전용).

    Blacklist 우선 → whitelist. 임시: 상수가 비어 있어 현재는 항상 None.
    실제 매핑은 별도 Task에서 채운다.

    Args:
        categories: 마켓이 속한 카테고리 문자열 집합.

    Returns:
        Classification 값 또는 None(UNKNOWN).
    """
    if categories & NON_MACRO_CATEGORIES:
        return Classification.NON_MACRO
    if categories & MACRO_CATEGORIES:
        return Classification.MACRO
    return None
```

---

## Port (신규 추가분만)

```python
# application/ports.py 에 추가 (기존 MarketSourcePort는 무변경)

class KalshiMarketSourcePort(Protocol):
    """Kalshi 마켓 데이터 소스."""

    async def fetch_active_markets(self, limit: int) -> list[KalshiMarketMetadata]:
        """활성 마켓 목록 fetch. 서버 사이드 정렬 없음(Kalshi API 제약)."""
        ...

    async def fetch_categories_bulk(self, series_ids: list[str]) -> dict[str, str]:
        """series_id → 주 카테고리 문자열 매핑."""
        ...
```

---

## Walking Skeleton — `KalshiMarketClient` 스텁

```python
# infrastructure/kalshi_client.py (신규 파일)

class KalshiMarketClient:
    """Kalshi KalshiMarketSourcePort 구현 — Walking Skeleton 스텁.

    하드코딩 응답만 반환한다. 실제 HTTP 호출은 후속 PR.
    """

    async def fetch_active_markets(self, limit: int) -> list[KalshiMarketMetadata]:
        return []

    async def fetch_categories_bulk(self, series_ids: list[str]) -> dict[str, str]:
        return {}
```

Integration test는 이 프로덕션 스텁이 아니라 **하드코딩된 값을 반환하는 Fake**(`_FakeKalshiSource`, 기존 `test_classifier_integration.py`의 `_FakeSource` 패턴과 동형)를 주입해 `fetch_active_markets → fetch_categories_bulk → classify_by_category` 흐름이 끊기지 않는지 검증한다. 저장(Repository)까지는 이 Slice 범위 밖이므로, 흐름의 마지막은 `classify_by_category()` 호출 결과 확인으로 끝난다.

---

## PR 순서 (TDD, 1 PR — 병존 추가라 분할 불필요)

**변경 사유**: 기존 계획(3 PR: Walking Skeleton → Domain → Port)은 "기존 타입 재설계"를 전제로 한 순서였다. 병존 추가 방식은 기존 코드를 전혀 건드리지 않는 순수 추가라 계층 간 의존성 충돌이 없다 — Domain(신규 타입) → Port(신규 Protocol) → classify_by_category → 스텁 → Integration test를 한 PR 안에서 자연스러운 TDD 순서(RED→GREEN)로 진행해도 충돌 위험이 없다.

### PR #1: Kalshi Walking Skeleton (병존 추가) — `feature/kalshi-market-source-acceptance`

1. **RED**: `tests/integration/market/test_kalshi_market_source_integration.py` 신설 — `_FakeKalshiSource` + `classify_by_category` 흐름 검증 (아직 타입 없어서 import 에러 = RED)
2. **GREEN 최소**: `domain/models.py`에 `KalshiMarketMetadata` 추가; `domain/classifier.py`에 `classify_by_category` + 빈 placeholder 상수 추가; `application/ports.py`에 `KalshiMarketSourcePort` 추가; `infrastructure/kalshi_client.py` 신설(스텁)
3. **Unit test**: `tests/unit/market/test_classifier.py`에 `classify_by_category` 케이스 추가(같은 파일, 기존 `TestClassify` 클래스는 무변경 — 새 `TestClassifyByCategory` 클래스만 추가) — "빈 상수 → 항상 None" 검증
4. **회귀 확인**: 기존 `test_classifier.py`(원래 클래스), `test_classifier_integration.py`, `test_polymarket_adapter.py`가 한 줄도 안 바뀐 채 그대로 green인지 diff로 확인

---

## 폴더 구조 (이 PR 완료 시, `+`는 추가·`=`는 무변경)

```
concenews-backend/
├─ src/modules/market/
│  ├─ domain/
│  │  ├─ models.py         (= 기존 클래스 무변경, + KalshiMarketMetadata)
│  │  └─ classifier.py     (= 기존 classify/상수 무변경, + classify_by_category, placeholder 상수)
│  ├─ application/
│  │  └─ ports.py          (= MarketSourcePort 무변경, + KalshiMarketSourcePort)
│  └─ infrastructure/
│     ├─ polymarket_client.py   (= 무변경)
│     └─ kalshi_client.py       (+ 신규, 스텁)
└─ tests/
   ├─ unit/market/
   │  └─ test_classifier.py     (= 기존 TestClassify 무변경, + TestClassifyByCategory)
   └─ integration/market/
      └─ test_kalshi_market_source_integration.py   (+ 신규)
```

---

## 의존성 변경

없음.

---

## PR 완료 조건 (Definition of Done)

- [ ] 신규 타입·함수 추가, 기존 Polymarket 코드·테스트 diff 0줄
- [ ] `test_kalshi_market_source_integration.py` GREEN
- [ ] `test_classifier.py`(기존 클래스), `test_classifier_integration.py`, `test_polymarket_adapter.py` 전부 그대로 green
- [ ] `just check-branch-green` green

## 후속 (참고)

- 실제 카테고리 매핑 확정 (별도 Task)
- Kalshi 실제 HTTP 구현 (Series→Event→Market 2단계 조회)
- Kalshi 분류 결과 저장 Service·Repository 배선 결정
- Polymarket 어댑터 제거 시점에 `Kalshi` 접두사 제거(리네임)
- `market-participant` 모듈 — 체결 규모 감지로 재정의
