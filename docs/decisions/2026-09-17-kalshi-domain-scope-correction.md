# ADR: Kalshi 이관 범위 정정 — Domain 재설계 필요 + 참여자 모듈 범위 축소

**Status**: Accepted
**Date**: 2026-09-17
**Slice**: Cross-cutting (market 모듈)

## Context

[2026-09-17 ADR: polymarket-to-kalshi-market-source-migration](./2026-09-17-polymarket-to-kalshi-market-source-migration.md)은 "`application/ports.py`의 Port 와 Domain 모델이 이미 거래소 비종속적이라 Infrastructure 어댑터만 교체하면 된다"고 전제했다. Walking Skeleton 착수 전 실제 코드를 확인한 결과 이 전제가 틀렸다:

- `MarketSourcePort.fetch_active_markets(limit, order, ascending)` — `order`/`ascending`은 서버 사이드 정렬을 전제하는데, Kalshi 는 [kalshi-api-contract.md](../../concenews-backend/docs/research/kalshi-api-contract.md) 실측대로 그런 정렬 파라미터가 없다.
- `MarketSourcePort.fetch_tags_bulk(condition_ids)` — `condition_id`는 Polymarket 고유 식별자 개념이고, "태그를 마켓에 직접 bulk 조회"하는 모양 자체가 Kalshi 구조(카테고리가 Market이 아니라 Event/Series 레벨)와 안 맞는다.
- Domain 모델 `Tag`(`Polymarket 태그`, `Gamma API 태그 ID`), `MarketMetadata`(`condition_id`, `Gamma API 마켓 메타데이터`), `MarketClassification`(`condition_id`) 전부 docstring 부터 필드명까지 Polymarket 전용이다.

또한 `market-participant` 모듈([ADR 2026-08-15](./2026-08-15-market-participant-observation-eligibility.md))은 Polymarket 온체인 지갑 공개성을 전제로 설계됐는데, Kalshi 는 `/portfolio/*` 전부 본인 인증 전용이라 지갑 단위 참여자 관측이 원천적으로 불가능함을 확인했다(같은 research 문서). 다만 `/markets/trades`의 `count_fp`·`is_block_trade`로 **개별 체결의 규모**(예: 한화 30억 상당 단일 베팅)는 신원 없이도 공개 관측 가능함을 추가로 확인했다.

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| A. 기존 Domain 모델 유지, 매핑 레이어로 흡수 | 코드 변경 최소 | 필드명·docstring 이 Polymarket 개념(condition_id, Gamma 태그)이라 매핑을 얹어도 의미가 왜곡됨. 다음 세션이 "왜 Kalshi 마켓에 condition_id가 있지"라고 혼란 |
| B. Domain 모델(Tag, MarketMetadata, MarketClassification)을 거래소 비종속 개념으로 재설계 | 실제 데이터 구조(카테고리가 Event/Series 레벨)를 정확히 반영. 향후 재교체 시에도 재사용 가능 | Domain 계약 변경이라 관련 Repository·Service 시그니처도 함께 손봐야 함 (별도 Spec/Plan에서 범위 확정) |
| C. Polymarket/Kalshi 멀티소스 병행 지원 설계 | 유연성 | 지금은 단일 소스(Kalshi)만 쓸 계획이라 과설계. YAGNI 위반 |

## Decision

**옵션 B 채택.**

- `Tag`·`MarketMetadata`·`MarketClassification`·`MarketSourcePort`는 Kalshi 실제 구조(카테고리 = Event/Series 레벨, 서버 사이드 정렬 없음, `condition_id` 같은 Polymarket 고유 개념 제거)에 맞춰 재설계한다. 구체 필드·시그니처는 이후 Spec/Plan에서 확정한다.
- `market-participant` 모듈은 **지갑 신원 기반 관측**(`ParticipantSourcePort`, `MarketParticipantObservationExclusion`) 범위를 폐기 대상으로 좁힌다. 대신 `/markets/trades`의 `count_fp`·`is_block_trade`를 이용한 **대형 체결(신규 유입) 감지**로 목적을 재정의한다 — 이건 참여자(누가) 개념이 아니라 마켓 자체의 체결 스트림 개념이므로, 새 Spec 단계에서 이 기능이 `market-participant` 모듈에 남을지 `market` 모듈로 흡수될지 모듈 경계를 다시 판단한다.

## Rationale

Port/Domain 계층이 실제로는 Polymarket 전용이었다는 사실을 구현 착수 전에 발견했으므로, 잘못된 전제 위에 Infrastructure 어댑터만 새로 얹는 것보다 Domain부터 다시 세우는 비용이 지금(코드 작성 전) 가장 싸다. 참여자 모듈은 전면 폐기 대신, 실제로 공개 데이터로 구현 가능한 부분(체결 규모 감지)과 불가능한 부분(신원 추적)을 분리해 가치를 최대한 보존한다.

## Reconsider When

- Kalshi가 향후 마켓 레벨에 카테고리 필드를 직접 노출하도록 API를 바꿀 때 (Series 조인 불필요해짐)
- Polymarket 재도입이 결정될 때 ([2026-09-10 ADR](./2026-09-10-polymarket-kr-block-response.md) 조건과 연동) — 이 경우 두 거래소 공통 Domain 설계가 다시 필요할 수 있음

## References

- [2026-09-17 ADR: polymarket-to-kalshi-market-source-migration](./2026-09-17-polymarket-to-kalshi-market-source-migration.md)
- [2026-08-15 ADR: market-participant-observation-eligibility](./2026-08-15-market-participant-observation-eligibility.md)
- [concenews-backend/docs/research/kalshi-api-contract.md](../../concenews-backend/docs/research/kalshi-api-contract.md)
- 2026-09-17 세션 실측: `src/modules/market/application/ports.py`, `src/modules/market/domain/models.py` 코드 직접 확인; Kalshi OpenAPI `Trade` 스키마(`count_fp`, `is_block_trade`) 확인
