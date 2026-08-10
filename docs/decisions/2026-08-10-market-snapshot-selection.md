# ADR: 시장 스냅샷 대상 선정과 데이터 소스

**Status**: Accepted
**Date**: 2026-08-10
**Slice**: market-snapshot-collection

## Context

마켓 분류 Slice는 활성 마켓을 MACRO/NON_MACRO로 분류해 저장한다. 다음 단계는 시장 변화의 근거가 될 확률·거래량 시계열을 수집하는 일이다. 모든 활성 마켓을 추적하면 유동성이 낮은 마켓의 노이즈와 저장 비용이 늘어난다.

실제 Gamma API Spike 결과, `volume24hr`로 활성 마켓을 정렬할 수 있고 상위 200개 중 128개가 현재 MACRO로 분류됐다. Gamma 응답에는 이 Slice에 필요한 결과별 확률, 최근 가격, 호가, 유동성과 기간별 거래량이 있다.

기존 [Polymarket API 선택 ADR](./2026-07-12-polymarket-api-choice.md)은 Gamma와 CLOB를 함께 언급하지만, 이번 Slice의 관측값 수집에는 Gamma만으로 충분하다.

## Options Considered

| 선택지 | 장점 | 단점 |
|---|---|---|
| 모든 활성 MACRO 마켓 추적 | 누락 최소화 | 낮은 유동성 노이즈와 비용 증가 |
| 상위 200 후보 중 MACRO 상위 50 추적 | 현재 관심도 중심, 비용 예측 가능 | 순위 밖 마켓은 추적하지 않음 |
| Gamma + CLOB 동시 수집 | 더 상세한 호가창 데이터 | 현재 목적 대비 외부 경계와 실패 지점 증가 |

## Decision

최근 24시간 거래량(`volume24hr`) 기준 활성 마켓 상위 200개를 후보군으로 조회한다. 유효한 MACRO 분류와 교집합한 뒤, 그 순서를 유지한 상위 50개를 5분마다 스냅샷한다.

스냅샷 데이터 소스는 Gamma API로 한정한다. CLOB 호가창과 거래 단위 데이터는 이상징후 분석에 실제로 필요해질 때 별도 Spike와 Slice로 도입한다.

## Rationale

- 최근 거래량은 누적 거래량보다 현재 시장 관심도를 잘 반영한다.
- 상위 200개는 현재 50개의 거시경제 대상 확보에 충분한 후보 폭을 제공한다.
- 상위 50개는 첫 운영 범위로 저장량과 외부 호출량을 제한하면서도, 실제 관찰 대상의 다양성을 확보한다.
- Gamma의 응답 필드만으로 확률·유동성·거래량 시계열의 첫 버전을 구성할 수 있다.

## Reconsider When

- 상위 200개 안의 MACRO 마켓이 50개 미만인 상태가 지속된다.
- 5분 해상도로는 의미 있는 변화를 놓친다는 근거가 생긴다.
- 호가 깊이 또는 체결 단위가 이상징후 판단에 필요해진다.
- 데이터 보존량 또는 수집 실패율이 운영 기준을 넘는다.

## References

- [Polymarket 시장 스냅샷 Spike](../research/polymarket-market-snapshot-contract.md)
- [시장 추적 Plan](../../concenews-backend/docs/plan-market-tracking.md)
- [Polymarket API 선택 ADR](./2026-07-12-polymarket-api-choice.md)
