# Polymarket 시장 스냅샷 Spike

## 질문

거시경제 마켓 중 최근 거래량이 높은 마켓 50개의 확률·유동성·거래량을 5분마다 저장하기 위해, Gamma API가 제공하는 필드와 페이지네이션 계약은 무엇인가?

## 실행일

2026-08-10

## 관찰

### 활성 마켓 조회와 정렬

- 엔드포인트는 `GET https://gamma-api.polymarket.com/markets`이다.
- `active=true`, `order=volume24hr`, `ascending=false` 조합으로 최근 24시간 거래량 내림차순의 활성 마켓을 조회할 수 있다.
- 한 요청의 실제 최대 반환 수는 100개였다. 따라서 상위 200개 후보군은 `limit=100, offset=0`과 `limit=100, offset=100` 두 페이지로 조회해야 한다.
- 2026-08-10 실행 시 상위 200개 중 기존 태그 분류 규칙상 MACRO는 128개, NON_MACRO는 66개, 미분류는 6개였다. 태그 조회 실패는 없었다.

### 스냅샷 필드

Gamma 시장 응답에 다음 필드가 존재했다.

| 용도 | 필드 | 관찰한 형식 |
|---|---|---|
| 식별 | `id`, `conditionId` | 문자열 |
| 질문 | `question` | 문자열 |
| 결과 이름 | `outcomes` | JSON 문자열 안의 문자열 배열 |
| 결과 확률 | `outcomePrices` | JSON 문자열 안의 숫자 문자열 배열 |
| 최근 가격 | `lastTradePrice` | 숫자 또는 null |
| 호가 | `bestBid`, `bestAsk`, `spread` | 숫자 또는 null |
| 유동성 | `liquidity` | 숫자 또는 null |
| 거래량 | `volume24hr`, `volume1wk`, `volume1mo` | 숫자 |
| 상태·종료 | `active`, `closed`, `endDate` | boolean, boolean, ISO 8601 UTC 문자열 |

`outcomes`, `outcomePrices`, `clobTokenIds`는 이미 배열이 아니라 JSON 문자열로 반환되는 사례를 확인했다. 어댑터가 이를 파싱하고, 숫자 문자열은 `float`로 변환해야 한다.

## 결정

1. 후보군은 최근 24시간 거래량 상위 활성 마켓 200개로 한다.
2. 후보군과 유효한 MACRO 분류를 교집합한 뒤, API의 `volume24hr` 내림차순을 유지해 상위 50개만 스냅샷한다.
3. 스냅샷 수집에는 Gamma API만 사용한다. CLOB 호가창은 이 Slice의 범위가 아니다.
4. 데이터가 50개 미만이면 가능한 마켓만 저장하고, 수집 자체는 실패하지 않는다.

## 구현 주의점

- 분류 수집 범위도 상위 200개로 확대해야 스냅샷 후보군과 분류 캐시의 범위가 일치한다.
- 외부 HTTP는 `httpx.MockTransport` fixture로 대체하고, 실제 Gamma API는 배포 전 수동 E2E로만 확인한다.
- 기존 `market_snapshot` 테이블은 이미 존재한다. Slice 구현에서 ORM·Repository·서비스를 추가하며, 동일 마켓의 서로 다른 수집 시각은 모두 보존한다.
