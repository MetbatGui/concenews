# Spec: 상위 보유 포지션 스냅샷 수집

**상태**: 검토 요청  
**Slice**: market-participant-snapshot

## 사용자 가치

사용자는 거래량 상위 매크로 마켓에서 공개적으로 관측되는 결과별 상위 보유 포지션을 시간순으로 확인할 수 있다. 이 데이터는 이후의 보유량 변화 신호를 검증할 수 있는 사실 기반이 된다.

## 범위

### 포함

- 최신 거래량 상위 매크로 마켓 스냅샷에서 추적 대상 최대 50개를 읽음
- 각 마켓의 `condition_id`로 Polymarket Data API 상위 보유자 조회
- 결과별 상위 20개 보유 포지션의 지갑 주소, 결과 인덱스, 원시 보유량, 관측 시각 저장
- 5분 주기의 별도 스케줄러 작업 등록
- 마켓 스냅샷에 Gamma `conditionId`를 함께 보존하는 마이그레이션

### 제외

- 보유량 변화 비교, 신규 상위권 진입·증가 신호 생성
- 거래 이력, 자금 출처, 손익, 지갑 소유자 추정
- ‘고래’, ‘전문 트레이더’, ‘내부자’, ‘대규모 자금’ 판정
- 참여자 정보를 사용자 계정이나 프로필 aggregate로 모델링

## 용어와 표현 원칙

- **상위 보유 포지션**: 특정 시점 Data API가 반환한 결과별 상위 보유자 목록의 한 항목이다.
- **원시 보유량**: API의 `amount` 값을 환산하지 않고 저장한 값이다. 금액·자금 규모로 표현하지 않는다.
- 지갑은 공개 `proxyWallet` 문자열만 저장한다. 표시 이름, 소개, 이미지 등 프로필 정보는 수집하지 않는다.

## Acceptance Criteria

### AC1. 추적 대상과 식별자 보존

- Gamma 응답의 숫자형 `id`와 `conditionId`가 마켓 스냅샷에 함께 보존된다.
- 기존 스냅샷 행은 마이그레이션 후에도 읽을 수 있다. `condition_id`가 없는 행은 참여자 수집 대상이 아니다.
- 참여자 수집은 가장 최근 수집 시점의 마켓별 스냅샷 중 `condition_id`가 있는 최대 50개만 대상으로 한다.

### AC2. Data API 변환과 저장

- 각 대상 마켓에 `GET /holders?market={conditionId}&limit=20`을 요청한다.
- 응답의 outcome token별 `holders` 항목에서 `proxyWallet`, `amount`, `outcomeIndex`를 변환한다.
- 각 보유 포지션은 마켓 숫자 ID, condition ID, 지갑, 결과 인덱스, 원시 보유량, UTC 관측 시각을 가진다.
- 동일 실행에서 반환된 모든 outcome token의 상위 보유 포지션을 저장한다. 이진 마켓은 결과당 20개, 최대 40개가 될 수 있다.
- 빈 응답은 정상이며 다른 마켓의 수집을 중단하지 않는다.

### AC3. 실행 경계와 실패 격리

- 별도 스케줄러가 기본 300초 주기로 참여자 수집 작업을 실행한다.
- 작업마다 DB Session과 HTTP client를 만들고 성공 시 commit, 실패 시 rollback 및 close한다.
- 한 마켓의 외부 API 실패는 기록 후 다음 마켓 수집을 계속한다. 작업 전체의 DB 실패는 rollback 후 다음 주기를 막지 않는다.

### AC4. 테스트 경계

- 원시 보유량 보존, 필수 식별자, 결과 인덱스 규칙은 Unit Test로 검증한다.
- 실제 PostgreSQL과 Domain·Repository·Service 조합은 Integration Test로 검증한다.
- Data API HTTP 경계는 Spike 기반 fixture와 `httpx.MockTransport`로 대체한다.
- 실제 Data API·실제 DB 검증은 `e2e` 마커의 수동 `just check-e2e`에만 둔다. `check-branch-green`에는 포함하지 않는다.

## 기술 결정

- 식별자 보존 결정은 [ADR: 마켓 스냅샷에 Polymarket condition ID를 함께 보존](../../docs/decisions/2026-08-10-market-participant-identity.md)을 따른다.
- 외부 응답 계약은 [Polymarket 참여자 Data API 계약](../../docs/research/polymarket-participant-data-contract.md)을 따른다.
- 대상 마켓 선택은 기존 [거래량 상위 마켓 선택 ADR](../../docs/decisions/2026-08-10-market-snapshot-selection.md)의 최신 스냅샷 결과를 재사용한다.
