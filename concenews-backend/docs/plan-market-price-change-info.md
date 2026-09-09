# Plan: 마켓 확률 변동 정보

**Spec**: [spec-market-price-change-info.md](./spec-market-price-change-info.md)
**상태**: 검토 요청

## 설계 요약

`MarketSnapshot` 에 nullable 필드 4개(`price_change_1h`, `price_change_24h`, `price_change_1w`, `price_change_1mo`)를 추가한다. 1w/1mo 는 Gamma 응답을 그대로 캡처하는 파싱 확장이고, 1h/24h 는 저장 시점에 자체 히스토리를 조회해 계산하는 별도 단계다.

```text
Gamma 응답 (oneWeekPriceChange, oneMonthPriceChange)
        ↓ 파싱 그대로 캡처
MarketSnapshotPayload
        ↓ to_snapshot()
MarketSnapshot (price_change_1w/1mo 채워짐, 1h/24h 는 아직 None)
        ↓ MarketSnapshotService.run() 에서 저장 직전
같은 market_id 의 과거 스냅샷 조회(-1h, -24h 시점에 가장 가까운 것)
        ↓ Yes 가격 차이 계산
최종 MarketSnapshot (4개 필드 전부 채워짐, 이력 없으면 NULL)
        ↓ save_bulk
```

## Task 1 — Gamma 1w/1mo 필드 캡처 + Migration

**브랜치/PR**: `feature/market-price-change-info-capture`

- `MarketSnapshotPayload`·`MarketSnapshot` 에 `price_change_1w`, `price_change_1mo` (둘 다 `float | None`) 추가
- `_parse_snapshot_payload()` 가 `oneWeekPriceChange`·`oneMonthPriceChange` 를 파싱하도록 확장
- `market_snapshot` 테이블에 4개 컬럼(`price_change_1h`, `price_change_24h`, `price_change_1w`, `price_change_1mo`, 전부 nullable float) 추가하는 Alembic 마이그레이션 — 1h/24h 컬럼도 이 Task 에서 함께 만든다(Task 2 가 채울 자리를 미리 마련)
- 실패하는 Unit Test 부터 — 파싱 함수가 두 필드를 정확히 뽑는지, 필드 누락 시 `None` 인지

**완료 기준**: `oneWeekPriceChange`·`oneMonthPriceChange` 가 있으면 그대로, 없으면 `None` 으로 파싱되고, `market_snapshot` 테이블에 4개 컬럼이 존재한다.

## Task 2 — 1h/24h 계산 + 저장 통합

**브랜치/PR**: `feature/market-price-change-info-lookback`

- `SnapshotRepositoryPort` 에 `find_closest_snapshot_before(market_id: str, target_time: datetime) -> MarketSnapshot | None` 추가
- `PgMarketSnapshotRepository` 구현 — `WHERE market_id = X AND timestamp <= target_time ORDER BY timestamp DESC LIMIT 1`
- Yes 가격 추출 헬퍼 — `outcomes` 튜플에서 `"Yes"` 라벨의 인덱스를 찾아 대응 가격 반환, 없으면 `None`(인덱스 0 을 가정하지 않음, Spec 표현 원칙)
- `MarketSnapshotService.run()` 수정 — 각 후보 스냅샷 저장 전에 `-1h`, `-24h` 조회를 수행해 `price_change_1h`, `price_change_24h` 를 채운다
- 실패하는 Integration Test 부터 — 실제 PostgreSQL 에 과거 스냅샷을 미리 저장해두고, 새 스냅샷 저장 후 1h/24h 값이 정확히 계산되는지, 비교할 과거 이력이 없으면 `NULL` 인지 검증

**완료 기준**: 과거 이력이 있으면 정확한 차이값, 없으면 `NULL`. 기존 `market_snapshot` 관련 테스트(Task 1 이전 것들) 는 그대로 GREEN 유지.

## 테스트 전략

Classicist 원칙에 따라 Domain, application service, PostgreSQL repository를 실제로 조합한다. 외부 HTTP 는 Fake source 로 대체한다.

## Definition of Done

- [ ] Task 1~2 PR이 각각 merge commit으로 `master`에 병합됨
- [ ] `just check-branch-green` 통과
- [ ] Gamma 제공 1w/1mo 값이 그대로 캡처됨을 테스트가 증명함
- [ ] 자체 계산한 1h/24h 값이 실제 히스토리 대비 정확함을 Integration Test가 증명함
- [ ] 이력 없는 구간은 `NULL` 임을 테스트가 증명함
