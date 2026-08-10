# Polymarket 참여자 Data API Spike

**실행일**: 2026-08-10

## 질문

마켓별 상위 보유자와 신규 대규모 자금 유입을 추적할 공개 데이터 계약이 있는가?

## 관찰

- `GET https://data-api.polymarket.com/holders?market={conditionId}&limit=5`가 200으로 응답했다.
- `market`에는 Gamma의 숫자 `id`가 아니라 `conditionId`를 넣어야 한다. 숫자 ID를 넣으면 `market` 파라미터 누락 400이 발생했다.
- 응답은 outcome token별 `holders` 배열이며, 각 보유자에 `proxyWallet`, `amount`, `outcomeIndex`, 공개 표시명 관련 필드가 있다.
- 따라서 특정 시점의 상위 보유 포지션은 수집할 수 있다.
- 신규 대규모 자금 유입은 단일 응답으로 판단할 수 없다. 동일 지갑·토큰의 연속 스냅샷 차이 또는 거래 이력 계약을 추가로 확인해야 한다.

## 결론

다음 Slice 후보는 `market-participant-snapshot`이다. 먼저 상위 보유 포지션을 주기적으로 저장하고, 신규 대규모 유입 감지는 관측값이 쌓인 뒤 별도 Slice로 분리한다.

## 구현 전 남은 확인

- 보유자 목록의 최대 페이지 크기와 페이지네이션
- 보유 금액의 단위 및 가격 환산 방식
- 거래 이력 API의 마켓·지갑 필터 계약과 최근성
- 공개 지갑 데이터를 다루는 표시·보존 정책
