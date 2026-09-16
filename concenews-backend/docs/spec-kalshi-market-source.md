# Spec: Kalshi 마켓 데이터 소스 전환 (Domain 재설계 + Walking Skeleton)

**상태**: Proposed
**Slice**: `kalshi-market-source`
**관련 결정**: [2026-09-17 polymarket-to-kalshi-market-source-migration](../../docs/decisions/2026-09-17-polymarket-to-kalshi-market-source-migration.md), [2026-09-17 kalshi-domain-scope-correction](../../docs/decisions/2026-09-17-kalshi-domain-scope-correction.md)
**참고**: [Kalshi API 계약 Spike](docs/research/kalshi-api-contract.md)

---

## 배경

기존 `market` 모듈의 Domain(`Tag`, `MarketMetadata`, `MarketClassification`)과 Port(`MarketSourcePort`)는 Polymarket 전용 개념(`condition_id`, 서버 사이드 `order`/`ascending` 정렬, 마켓에 직접 붙은 태그 bulk 조회)으로 설계돼 있다. Kalshi는 구조가 다르다 — 카테고리는 Market이 아니라 Event/Series 레벨에 있고, 서버 사이드 정렬이 없다.

이 Slice는 Domain을 Kalshi 실제 구조에 맞게 재설계하고, `KalshiMarketClient`로 Walking Skeleton까지 완성한다. 분류 로직 자체(무엇이 MACRO 인지)의 재조정은 범위 밖 — 기존 blacklist/whitelist 방식의 골격만 새 카테고리 문자열 기준으로 옮긴다.

## 사용자 스토리

> 시스템은 Kalshi 공개 API에서 활성 마켓과 카테고리 정보를 가져와, 기존과 동일하게 MACRO/NON_MACRO로 분류하고 캐싱한다 — 데이터 출처가 Polymarket에서 Kalshi로 바뀌었을 뿐 분류 결과의 소비 방식(다운스트림)은 변하지 않는다.

## 범위

### 포함

- Domain 재설계: `MarketMetadata`, `Category`(구 `Tag` 대체), `MarketClassification`을 Kalshi 개념(ticker, series_ticker, category 문자열)으로 재정의
- `MarketSourcePort` 재설계: 서버 사이드 정렬 파라미터 제거, 카테고리 조회를 series 단위로 변경
- `KalshiMarketClient` Walking Skeleton: 하드코딩 스텁으로 Integration test GREEN
- `docs/research/kalshi-api-contract.md`에서 확인한 2단계(Series→Event→Market) 조회 흐름을 어댑터 인터페이스에 반영(스텁 단계에선 실제 HTTP 호출 없음)

### 제외

- `KalshiMarketClient`의 실제 HTTP 구현 (후속 PR, Walking Skeleton은 스텁만)
- `classify()` 함수의 실제 MACRO/NON_MACRO 카테고리 목록 확정 (기존 tag ID 상수를 Kalshi 카테고리 문자열로 1:1 매핑하는 작업은 별도 스파이크성 조사 필요 — 이 Slice는 자료구조만 바꾸고 목록은 placeholder로 둠)
- `market-participant` 모듈 재설계 (별도 Slice, [ADR 2026-09-17](../../docs/decisions/2026-09-17-kalshi-domain-scope-correction.md) 범위)
- Polymarket 전용 Infrastructure 파일 제거 (사용자 지시로 보류 — 작업 트리에 남겨둠, 미사용 경로로 유지)
- "주요 마켓" 클라이언트 사이드 랭킹(`/series?include_volume=true` 활용) 구현 — 별도 Slice

## Acceptance Criteria

### AC1. Domain 모델

- `MarketMetadata`: `market_id`(Kalshi ticker), `series_id`(Kalshi series_ticker), `question`, `end_date` 필드를 갖는다. `condition_id`·Polymarket 언급이 없다.
- `Category`: `id`(카테고리 문자열, 예: `"Economics"`)만 있으면 충분 — Kalshi 카테고리는 정수 ID가 아니라 문자열이므로 `Tag`의 `int id`/`slug` 구조를 유지하지 않는다.
- `MarketClassification`: `market_id`, `question`, `classification`, `categories`(문자열 튜플), `end_date`, `classified_at`로 재정의한다.
- 기존 `Classification` enum(`MACRO`/`NON_MACRO`)은 그대로 유지한다.

### AC2. Port

- `MarketSourcePort.fetch_active_markets(limit: int) -> list[MarketMetadata]` — `order`/`ascending` 파라미터를 제거한다(Kalshi에 대응 기능 없음).
- `MarketSourcePort.fetch_categories_bulk(series_ids: list[str]) -> dict[str, str]` — series_id → 주 카테고리 문자열 매핑. 기존 `fetch_tags_bulk(condition_ids) -> dict[str, list[Tag]]`을 대체한다.

### AC3. Walking Skeleton

- `KalshiMarketClient`(하드코딩 스텁)가 `MarketSourcePort`를 구현한다.
- Integration test가 스텁 상태로 GREEN: 활성 마켓 목록 fetch → series→category 매핑 조회 → 분류 저장까지 하나의 흐름이 끊기지 않고 동작함을 증명한다(값 자체는 스텁 하드코딩).
- 기존 `PolymarketGammaClient` 및 그 사용처는 변경하지 않는다(제거는 이 Slice 범위 밖).

### AC4. 검증

- `just check-branch-green` 통과.
- 신규 Domain 모델·Port에 Polymarket 관련 문자열(`condition_id`, `Gamma`, `Polymarket`)이 남아있지 않음을 리뷰에서 확인한다.

## 설계 제약

- `classify()` pure function의 시그니처는 `set[int]`(태그 ID) → `set[str]`(카테고리 문자열)로 바뀐다. 기존 blacklist/whitelist 상수(`NON_MACRO_IDS`, `MACRO_IDS`)는 이 Slice에서 실제 값 채우기를 하지 않고 빈 placeholder로 둔다 — 실제 매핑은 Kalshi 카테고리 목록을 다시 조사해야 하므로 별도 작업.
- `MarketClassifierService`의 흐름(캐시 조회 → 신규 fetch → 분류 → 저장)은 이 Slice에서 구조 변경 없이 재사용한다. 태그 bulk 조회가 series 단위 카테고리 조회로 바뀌는 것만 반영한다.
- DB 스키마(`market_classification` 테이블)의 `condition_id` 컬럼명 변경 여부는 이 Slice 범위 밖 — 기존 컬럼명 유지, 애플리케이션 레벨에서만 `market_id`로 부른다(컬럼명까지 바꾸려면 마이그레이션이 추가로 필요해 별도 판단 필요).

## 완료 조건

- Domain·Port가 Kalshi 구조로 재정의되고 Polymarket 전용 개념이 프로덕션 코드에서 제거된다.
- `KalshiMarketClient` 스텁이 Walking Skeleton Integration test를 통과한다.
- 로컬 품질 게이트 green.

## 참고

- [Kalshi API 계약 Spike](docs/research/kalshi-api-contract.md)
- [기존 매크로 마켓 분류 Plan (Polymarket 버전, 구조 참고용)](plan-market-tracking.md)
