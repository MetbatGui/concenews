# ADR: 마켓 참여자 관측 자격을 원본 스냅샷과 분리

**Status**: Accepted
**Date**: 2026-08-15
**Slice**: market-participant-observation-eligibility

## Context

Polymarket Data API의 상위 보유자 응답은 지갑별 결과 토큰 잔고만 제공한다. 조건부 토큰은 거래소 체결뿐 아니라 split, merge, Neg Risk conversion으로도 생성·이동한다. 따라서 대규모 잔고를 일반 참여자의 방향성 거래나 자금 유입으로 곧바로 해석하면 잘못된 신호가 만들어질 수 있다.

Spike에서 확인한 `0xa5ef39c3d3e10d0b270233af41cac69796b12966`은 2026년 9월 FOMC 결과 마켓의 모든 `No` 결과에 동일한 대규모 잔고를 보유한다. 공개 거래 이력 없이 Polymarket Neg Risk Adapter 흐름에서 토큰을 수령한다. 공개 데이터만으로 소유자가 Polymarket인지 확정할 수는 없지만, 일반 거래 참여자 신호로 귀속할 수는 없다.

Spike 근거: [Polymarket 시스템성 지갑 관측 자격](../research/polymarket-system-wallet-eligibility.md)

## Options Considered

| 옵션 | 장점 | 단점 |
| --- | --- | --- |
| 수집 단계에서 제외하고 원본을 저장하지 않음 | 이후 조회가 단순함 | 관측 근거와 제외 판단을 재검증할 수 없음 |
| 원본을 수정·삭제해 순위만 보존 | 저장량이 작음 | 외부 관측값을 훼손하고 정책 변경 시 복구할 수 없음 |
| 원본과 관측 자격을 분리하고, 명시적 제외 목록을 신호 단계에 적용 | 근거 재현·정책 변경·감사가 가능함 | 조회와 신호 계산에 자격 필터가 추가됨 |
| 패턴 탐지로 즉시 자동 영구 제외 | 운영 개입이 적음 | 일반 참여자를 잘못 배제할 위험이 큼 |

## Decision

모든 Data API 상위 보유자 응답은 원본 `MarketParticipantSnapshot`으로 보존한다. 원본 수집 단계는 지갑을 제외하거나 순위를 재계산하지 않는다.

신호와 사용자용 상위 참여자 조회에는 별도의 관측 자격 정책을 적용한다. 제외 목록에는 지갑 주소, 제외 사유, 근거 URL, 등록일, 검토 상태를 보존한다. 초기 목록에는 Spike 대상 지갑을 등록한다.

자동 탐지는 제외 후보를 제안하는 데만 사용한다. 후보는 공개 거래 근거 부재와 동일 Neg Risk 이벤트 전반의 기계적 대규모 잔고 같은 감사 가능한 근거를 갖춰야 하며, 사람의 검토 없이 영구 제외하지 않는다.

제품 표현은 소유자·운영 주체·마켓메이커 여부를 단정하지 않는다. 제외 사유는 `거래 참여자로 귀속할 수 없는 지갑`으로 한정한다.

## Rationale

원본과 해석 정책을 분리하면 외부 데이터 계약을 보존하면서도, 제품 신호의 품질을 높일 수 있다. 정책이 바뀌어도 원본 스냅샷을 다시 수집하지 않고 신호를 재계산할 수 있으며, 특정 지갑이 왜 제외됐는지도 검증 가능하다.

자동 영구 제외 대신 사람 검토를 요구하면, 공개 데이터의 불완전성으로 일반 참여자를 부당하게 배제하는 위험을 낮춘다.

## Reconsider When

- Polymarket이 시스템·정산 지갑의 공식 목록이나 역할 메타데이터를 제공할 때
- 공개 체결 데이터만으로 지갑의 maker·taker·conversion 활동을 신뢰성 있게 구분할 수 있을 때
- 제외 목록의 수동 검토 비용이 실제 운영 한계를 넘을 때

## References

- [Polymarket 시스템성 지갑 관측 자격 Spike](../research/polymarket-system-wallet-eligibility.md)
- [마켓 스냅샷에 Polymarket condition ID를 함께 보존](./2026-08-10-market-participant-identity.md)
- [Polymarket Negative Risk Markets](https://docs.polymarket.com/advanced/neg-risk)
