# Spec: Kalshi 마켓 데이터 소스 전환 (Domain 병존 추가 + Walking Skeleton)

**상태**: Proposed
**Slice**: `kalshi-market-source`
**관련 결정**: [2026-09-17 polymarket-to-kalshi-market-source-migration](../../docs/decisions/2026-09-17-polymarket-to-kalshi-market-source-migration.md), [2026-09-17 kalshi-domain-scope-correction](../../docs/decisions/2026-09-17-kalshi-domain-scope-correction.md)
**참고**: [Kalshi API 계약 Spike](docs/research/kalshi-api-contract.md)

---

## 배경

기존 `market` 모듈의 Domain(`Tag`, `MarketMetadata`, `MarketClassification`)과 Port(`MarketSourcePort`)는 Polymarket 전용 개념(`condition_id`, 서버 사이드 `order`/`ascending` 정렬, 마켓에 직접 붙은 태그 bulk 조회)으로 설계돼 있다. Kalshi는 구조가 다르다 — 카테고리는 Market이 아니라 Event/Series 레벨에 있고, 서버 사이드 정렬이 없다.

**초안에서는 기존 타입을 Kalshi 구조로 "재설계"(필드 rename)하려 했으나, 구현 착수 전 검토에서 이게 `PolymarketGammaClient`·`MarketClassifierService`·기존 테스트 스위트를 전부 건드리는 것으로 드러났다** — `MarketMetadata`/`Tag`/`MarketClassification`/`classify()`는 전부 지금도 프로덕션에서 쓰이는 Polymarket 흐름의 실제 타입이라, 필드명이나 시그니처를 바꾸면 그 흐름 자체가 깨진다(특히 `classify()`를 `int` 태그ID → `str` 카테고리로 바꾸면 `NON_MACRO_IDS`/`MACRO_IDS`의 실측값이 무의미해져 Polymarket 분류가 전부 UNKNOWN이 되는 회귀가 생긴다).

그래서 이 Slice는 **기존 Polymarket 타입을 전혀 건드리지 않고, Kalshi 전용 타입을 추가(additive)** 하는 방식으로 바꾼다. "거래소 비종속 Domain"이라는 원래 지향점은 이후 Polymarket 어댑터를 실제로 제거하는 시점에 재추구한다(그때는 병존시킬 대상이 없어 안전하게 리네임 가능).

## 사용자 스토리

> 시스템은 Kalshi 공개 API에서 활성 마켓과 카테고리 정보를 가져와, 기존 Polymarket 분류 흐름과 동일한 개념(MACRO/NON_MACRO)으로 분류할 수 있는 기반을 갖춘다 — Polymarket 흐름은 이 Slice로 인해 전혀 변하지 않는다.

## 범위

### 포함

- 신규 Domain 타입(기존 타입과 별개, 병존): `KalshiMarketMetadata`(ticker/series_ticker/question/end_date), `KalshiCategory`(문자열 id)
- 신규 `KalshiMarketSourcePort`(기존 `MarketSourcePort`와 별개 Protocol): 서버 사이드 정렬 파라미터 없음, series 단위 카테고리 조회
- `domain/classifier.py`에 `classify_by_category(categories: set[str]) -> Classification | None` 신규 함수 + `NON_MACRO_CATEGORIES`/`MACRO_CATEGORIES`(빈 placeholder) 추가 — 기존 `classify()`/`NON_MACRO_IDS`/`MACRO_IDS`는 무변경
- `KalshiMarketClient` Walking Skeleton: 하드코딩 스텁으로 Integration test GREEN

### 제외

- `KalshiMarketClient`의 실제 HTTP 구현 (후속 PR, Walking Skeleton은 스텁만)
- 실제 Kalshi MACRO/NON_MACRO 카테고리 목록 확정 — **별도 Task로 분리**. 이 Slice는 자료구조와 빈 placeholder만 만든다.
- `market-participant` 모듈 재설계 (별도 Slice, [ADR 2026-09-17](../../docs/decisions/2026-09-17-kalshi-domain-scope-correction.md) 범위)
- 기존 `MarketMetadata`/`Tag`/`MarketClassification`/`classify()`/`MarketSourcePort`/`PolymarketGammaClient`의 변경 — **전부 무변경 유지**
- `MarketClassifierService`를 Kalshi로 연결하는 새 Service/Repository 배선 — 이 Slice는 Domain·Port·스텁 어댑터까지만. 실제로 분류 결과를 저장하는 Service·DB 스키마 연결은 후속 Slice(실 HTTP 구현과 함께 결정)
- "주요 마켓" 클라이언트 사이드 랭킹(`/series?include_volume=true` 활용) 구현 — 별도 Slice

## Acceptance Criteria

### AC1. Domain 모델 (신규, 병존)

- `KalshiMarketMetadata`: `market_id`(ticker), `series_id`(series_ticker), `question`, `end_date` 필드.
- `KalshiCategory`: `id: str`(예: `"Economics"`) — Kalshi 카테고리는 문자열이라 `Tag`의 `int id`/`slug` 구조를 따르지 않는다.
- 기존 `MarketMetadata`, `Tag`, `MarketClassification`, `Classification` enum은 **파일·필드 그대로**.

### AC2. Port (신규, 병존)

- `KalshiMarketSourcePort.fetch_active_markets(limit: int) -> list[KalshiMarketMetadata]` — 정렬 파라미터 없음.
- `KalshiMarketSourcePort.fetch_categories_bulk(series_ids: list[str]) -> dict[str, str]` — series_id → 주 카테고리 매핑.
- 기존 `MarketSourcePort`는 무변경.

### AC3. classify_by_category (신규, 병존)

- `classify_by_category(categories: set[str]) -> Classification | None` — 기존 `classify()`와 동일한 blacklist-우선 로직 구조.
- `NON_MACRO_CATEGORIES`/`MACRO_CATEGORIES`는 빈 `frozenset[str]`로 시작 — 이 Slice가 끝나도 실질적으로 항상 `None` 반환. Unit test가 이 계약("빈 상수 상태에서 항상 None")을 명시적으로 검증한다.
- 기존 `classify()`, `NON_MACRO_IDS`, `MACRO_IDS`는 **무변경**.

### AC4. Walking Skeleton

- `KalshiMarketClient`(하드코딩 스텁)가 `KalshiMarketSourcePort`를 구현한다.
- Integration test가 스텁 상태로 GREEN: `fetch_active_markets` → `fetch_categories_bulk` → `classify_by_category` 순서로 하나의 흐름이 끊기지 않고 동작함을 증명한다(저장까지는 이 Slice 범위 밖 — Repository/Service 연결 없음).

### AC5. 회귀 없음 검증

- 기존 `tests/unit/market/test_classifier.py`, `tests/integration/market/test_classifier_integration.py`, `tests/unit/market/test_polymarket_adapter.py`가 **한 줄도 변경 없이** 그대로 통과한다.
- `just check-branch-green` 통과.

## 설계 제약

- Domain 타입 병존은 임시 상태다 — Polymarket 어댑터를 실제로 제거하는 시점([2026-09-17 마이그레이션 ADR](../../docs/decisions/2026-09-17-polymarket-to-kalshi-market-source-migration.md) Migration Path 3번)에 `Kalshi` 접두사를 뗀 이름으로 정리한다(그때는 병존 대상이 없어 단순 rename 가능). 지금 접두사를 붙이는 건 영구 네이밍이 아니라 회귀 방지를 위한 임시 조치임을 코드 주석·docstring에 남긴다.
- 실제 카테고리 매핑(무엇이 MACRO/NON_MACRO 인지)은 별도 Task로 분리한다 — 이 Slice의 Definition of Done에 포함하지 않는다.

## 완료 조건

- 신규 Kalshi 전용 Domain·Port·classify_by_category가 추가되고, 기존 Polymarket 코드·테스트는 전혀 변경되지 않는다.
- `KalshiMarketClient` 스텁이 Walking Skeleton Integration test를 통과한다.
- 로컬 품질 게이트 green.

## 참고

- [Kalshi API 계약 Spike](docs/research/kalshi-api-contract.md)
- [기존 매크로 마켓 분류 Plan (Polymarket 버전, 구조 참고용)](plan-market-tracking.md)
