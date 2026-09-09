# ADR: 마켓 확률 변동 정보의 구간별 소싱 방식

**Status**: Accepted
**Date**: 2026-09-10
**Slice**: market-price-change-info

## Context

`MarketSnapshot` 에 확률(Yes 가격) 변동 정보를 4개 구간(1h, 24h, 1w, 1mo)으로 추가한다. 구간마다 데이터 확보 방식이 다르다.

- Polymarket Gamma API `/markets` 응답에 `oneWeekPriceChange`·`oneMonthPriceChange` 필드가 이미 계산되어 포함된다. `oneDayPriceChange`·`oneHourPriceChange` 같은 필드는 존재하지 않는다(원본 필드 덤프로 확인).
- 우리 `market_snapshot` 은 5분 주기로 수집돼, 1시간·24시간 전 시점에 가장 가까운 과거 스냅샷을 자체 히스토리에서 찾아 비교할 수 있다.
- 이 프로젝트의 수집 이력은 아직 짧다(수 주 수준). 1주·1개월 변동을 자체 히스토리로 재구성하면, 그 기간만큼 데이터가 쌓이기 전까지는 부정확하거나 결측된다.

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| A. 4개 구간 전부 자체 히스토리로 계산 | 소싱 방식이 하나로 통일됨 | 1주·1개월은 그만큼 이력이 쌓이기 전까지 부정확/결측. Gamma 가 이미 정확히 계산해 제공하는 값을 버리는 셈 |
| B. 4개 구간 전부 Gamma 필드 사용 | 구현 단순 | 1시간·24시간에 대응하는 Gamma 필드 자체가 없음 — 불가능 |
| C. 이원화: 1h/24h 자체 계산, 1w/1mo Gamma 필드 캡처 | 각 구간을 가장 정확한 소스로 채움. 처음부터 1w/1mo 정확 | 소싱 방식이 구간마다 달라 일관성이 떨어져 보임 |

## Decision

**옵션 C 채택.**

- `price_change_1h`, `price_change_24h`: 저장 시점에 같은 `market_id` 의 과거 스냅샷 중 목표 시각(now-1h, now-24h)에 가장 가까운 것을 조회해 현재 Yes 가격과 비교해 계산한다.
- `price_change_1w`, `price_change_1mo`: Gamma 응답의 `oneWeekPriceChange`·`oneMonthPriceChange` 를 그대로 캡처한다. 재계산하지 않는다.
- 임계값·알림은 없다. 신호 판정이 아니라 순수 변동폭 정보 제공이다.

## Rationale

옵션 A(통일된 자체 계산)는 일관성은 있어 보이지만 실제로는 더 나쁘다 — 이 프로젝트의 수집 이력이 1개월에 훨씬 못 미치는 지금, 자체 계산한 1개월 변동은 결측이거나 왜곡된다. Gamma 가 이미 자신의 더 긴 내부 데이터로 정확히 계산해 제공하는 값을 버리고 열등한 자체 근사치로 대체할 이유가 없다.

옵션 B 는 애초에 존재하지 않는 필드를 전제해 성립하지 않는다.

이원화가 "지저분해 보인다" 는 우려는 실익보다 미학적 우려다. 각 구간을 가장 정확하게 만들 수 있는 소스를 쓰는 것이 옳다.

## Reconsider When

- 자체 수집 이력이 1개월을 안정적으로 초과해 자체 계산 정확도가 Gamma 제공값과 사실상 동등해질 때 (그래도 굳이 바꿀 실익은 크지 않다 — Gamma 값이 이미 정확하다면 유지 비용만 늘어난다)
- Gamma API 가 `oneWeekPriceChange`·`oneMonthPriceChange` 필드를 제공 중단할 때

## References

- [spec-market-price-change-info.md](../../concenews-backend/docs/spec-market-price-change-info.md)
- `concenews-backend/src/modules/market/infrastructure/polymarket_client.py` — Gamma 원본 필드 확인
