# ADR: 마켓 스냅샷에 Polymarket condition ID를 함께 보존

**Status**: Proposed  
**Date**: 2026-08-10  
**Slice**: market-participant-snapshot

## Context

현재 `market_snapshot.market_id`에는 Gamma API의 숫자형 `id`가 저장된다. 그러나 Data API의 상위 보유자 endpoint는 같은 마켓을 `conditionId`로 식별한다. 숫자형 `id`를 전달하면 요청이 성립하지 않는다.

참여자 보유 포지션은 마켓 스냅샷이 이미 선택한 거래량 상위 매크로 마켓을 대상으로 수집해야 한다. 따라서 실행 시마다 별도의 마켓 탐색으로 두 식별자를 다시 연결하면 선택 규칙이 중복되고, 과거 관측과 외부 응답의 추적 가능성이 떨어진다.

Spike 근거: [Polymarket 참여자 Data API 계약](../research/polymarket-participant-data-contract.md)

## Options Considered

| 옵션 | 장점 | 단점 |
| --- | --- | --- |
| 마켓 스냅샷에 `condition_id`를 추가 | 선택된 마켓과 참여자 API 입력을 동일 관측에 보존하며, 이후 조회가 단순함 | 스키마·도메인 모델 마이그레이션 필요 |
| 참여자 수집 때 Gamma API를 다시 조회 | 기존 테이블 변경 없음 | 선택 규칙과 외부 호출이 중복되고 시점이 어긋날 수 있음 |
| 숫자형 `market_id`만 사용 | 구현 변경이 가장 작음 | Data API 계약과 호환되지 않아 불가능 |

## Decision

`MarketSnapshot`과 `market_snapshot`에 불변 외부 식별자인 `condition_id`를 추가한다. Gamma 응답의 `conditionId`를 그대로 저장하며, 기존 `market_id`는 Gamma의 숫자형 `id`로 계속 보존한다.

참여자 수집기는 가장 최근에 저장된 추적 대상 마켓 스냅샷에서 `market_id`와 `condition_id`를 함께 읽고, Data API에는 후자만 전달한다.

기존 행은 `condition_id`가 없을 수 있으므로 새 컬럼은 과거 행에 대해 nullable로 마이그레이션한다. 참여자 수집의 대상은 `condition_id`가 있는 최신 스냅샷으로 한정한다.

## Rationale

두 API가 요구하는 식별자를 같은 관측 레코드에 남기면, 참여자 스냅샷이 어떤 마켓 선택 결과에서 비롯됐는지 재현할 수 있다. 이는 외부 API를 별도 인프라 경계로 유지하면서도 선택 규칙의 중복을 막는다.

## Reconsider When

- Gamma가 `id`와 `conditionId`의 관계 또는 Data API 입력 계약을 변경할 때
- 마켓 식별자를 별도 정규화 aggregate로 승격할 때

## References

- [Polymarket 참여자 Data API 계약](../research/polymarket-participant-data-contract.md)
- [거래량 상위 마켓 선택 ADR](./2026-08-10-market-snapshot-selection.md)
