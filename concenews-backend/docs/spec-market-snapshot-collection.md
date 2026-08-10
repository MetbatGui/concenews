# Spec: 거래량 상위 거시경제 마켓 스냅샷 수집

**상태**: 승인됨
**Slice**: market-snapshot-collection

## 사용자 가치

시스템은 현재 거래가 활발한 거시경제 예측 마켓의 확률·유동성·거래량 변화를 시간순으로 보존한다. 이후 뉴스-마켓 매칭과 이상징후 탐지가 검증 가능한 시장 데이터에 근거할 수 있다.

## 범위

### 포함

- Gamma API에서 최근 24시간 거래량 상위 활성 마켓 200개 조회
- 유효한 MACRO 분류 마켓만 남긴 뒤 상위 50개 선정
- 선정 마켓의 확률, 최근 가격, 호가, 유동성, 최근 24시간·1주·1개월 거래량과 수집 시각 저장
- 5분 주기의 별도 Scheduler 작업 등록
- 분류 수집 범위를 상위 200개로 확대

### 제외

- CLOB 호가창·체결 이력 수집
- 스파이크 또는 이상징후 판단
- 마켓 조회 HTTP API와 화면
- 뉴스-마켓 매칭

## Acceptance Criteria

### AC1. 후보군과 대상 선정

- Gamma API를 `active=true`, `order=volume24hr`, `ascending=false`로 두 페이지 조회해 활성 마켓 최대 200개를 얻는다.
- `market_classification`에 유효한 `MACRO` 분류가 있는 마켓만 대상으로 남긴다.
- API 정렬 순서를 보존해 처음 50개를 선정한다.
- 대상이 50개 미만이면 가능한 수만 저장하고 오류로 처리하지 않는다.

### AC2. 스냅샷 저장

- 각 대상마다 `market_snapshot`에 한 행을 저장한다.
- 행에는 시장 식별자, 질문, 결과 이름·확률, 가격·호가·스프레드, 유동성, 최근 24시간·1주·1개월 거래량, 종료 시각, 상태, UTC 수집 시각이 포함된다.
- JSON 문자열인 결과 이름·확률은 각각 배열과 숫자 배열로 변환해 저장한다.
- 동일 마켓의 서로 다른 수집 시각은 모두 보존한다.

### AC3. 주기 실행과 자원 정리

- Scheduler 컨테이너가 300초마다 스냅샷 작업을 실행한다.
- 작업마다 새 DB Session과 HTTP 클라이언트를 만들고, 성공·실패와 관계없이 닫는다.
- 외부 API 또는 DB 실패는 작업 단위로 기록하며 다음 주기 실행을 막지 않는다.

### AC4. 테스트 경계

- Domain 선정 규칙과 변환은 Unit Test로 검증한다.
- 실제 PostgreSQL과 서비스 조합은 Integration Test로 검증한다.
- Gamma HTTP는 모든 자동 테스트에서 fixture 기반 `httpx.MockTransport`로 대체한다.
- 실제 Gamma API 검증은 `just check-e2e`에 넣지 않고 배포 전 수동 검증으로 유지한다.

## 기술 결정

- 대상 선정과 데이터 소스는 [ADR: 시장 스냅샷 대상 선정과 데이터 소스](../../docs/decisions/2026-08-10-market-snapshot-selection.md)를 따른다.
- 실제 API 계약은 [Polymarket 시장 스냅샷 Spike](../../docs/research/polymarket-market-snapshot-contract.md)를 따른다.
