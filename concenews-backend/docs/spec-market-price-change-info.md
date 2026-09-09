# Spec: 마켓 확률 변동 정보

**상태**: 검토 요청
**Slice**: market-price-change-info

## 사용자 가치

사용자는 특정 마켓의 확률이 최근 얼마나 움직였는지 여러 시간 축(1시간·24시간·1주·1개월)으로 한눈에 볼 수 있다. 임계값 판정이나 알림 없이, 있는 그대로의 변동폭 정보를 제공해 사용자가 스스로 중요도를 판단하게 한다.

## 범위

### 포함

- 마켓 스냅샷 저장 시 Yes 가격의 1시간·24시간 변동을 자체 히스토리 조회로 계산해 함께 저장
- Gamma API 가 제공하는 1주·1개월 변동(`oneWeekPriceChange`, `oneMonthPriceChange`)을 그대로 캡처해 저장
- 비교 대상 스냅샷이 아직 없는 신규 마켓·구간은 해당 값을 결측(NULL)으로 남김

### 제외

- 임계값 기반 신호 판정·알림 (`docs/decisions/2026-09-10-price-change-info-sourcing.md` 결정)
- 거래량 변동 (별도 후속 Slice)
- 조회 API·프론트엔드 표시
- 참여자 포지션 기반 신호 (별도 Slice)

## 용어와 표현 원칙

- **변동폭**: 현재 Yes 가격 - 비교 시점 Yes 가격. 부호 있는 값(양수=상승, 음수=하락).
- **Yes**: `outcomes` 튜플에서 `"Yes"` 라벨을 가진 인덱스의 가격. 인덱스 0 을 가정하지 않는다.
- 결측은 "변동 없음(0)" 이 아니라 "비교 불가" 를 뜻한다 — 값이 없으면 그 구간을 계산할 이력이 아직 없다는 뜻이다.

## Acceptance Criteria

### AC1. 1h/24h 변동 계산

- 새 스냅샷 저장 시, 같은 `market_id` 의 과거 스냅샷 중 목표 시각(현재-1시간, 현재-24시간)에 가장 가까운 것을 찾아 Yes 가격 차이를 계산한다.
- 목표 시각보다 오래된 스냅샷이 하나도 없으면 해당 구간 값은 `NULL` 이다.
- 목표 시각에 정확히 일치하는 스냅샷이 없어도, 가장 가까운 과거 스냅샷을 사용한다(5분 주기 수집이라 정확히 일치할 일은 드묾).

### AC2. 1w/1mo 변동 캡처

- Gamma API 응답의 `oneWeekPriceChange`·`oneMonthPriceChange` 를 그대로 저장한다. 자체 계산하지 않는다.
- 두 필드가 응답에 없으면(`null` 또는 누락) 저장값도 `NULL` 이다.

### AC3. 기존 계약 불변

- 기존 `MarketSnapshot` 필드(가격, 거래량, active/closed 등)는 이 Slice 로 변경되지 않는다.
- 필드 추가는 전부 nullable — 기존 스냅샷 행이나 이 값을 안 쓰는 코드에 영향 없음.

### AC4. 테스트 경계

- 1h/24h 계산 로직은 실제 PostgreSQL 히스토리 조회를 포함하므로 Integration Test 로 검증한다.
- 1w/1mo 캡처는 파싱 로직이라 Unit Test 로 검증한다.
- 외부 HTTP 는 Fake source 로 대체한다.

## 기술 결정

- 구간별 소싱 이원화: [ADR 2026-09-10](../../docs/decisions/2026-09-10-price-change-info-sourcing.md)
- Gamma 원본 필드 확인: [Spike: Gamma API 가격 변동 필드](../../docs/research/gamma-price-change-fields.md)
