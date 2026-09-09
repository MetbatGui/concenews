# Gamma API 가격 변동 필드 Spike

**실행일**: 2026-09-10

## 질문

`market-price-change-info` Slice 설계 중, Polymarket Gamma API `/markets` 응답에 구간별(1h/24h/1w/1mo) 가격 변동이 이미 계산되어 오는 필드가 있는지 확인.

## 방법

`GET /markets` 응답 마켓 객체 하나에서 `"price"` 또는 `"outcome"` 을 포함하는 키를 전부 추출.

## 결과

```
관련 필드: ['outcomes', 'outcomePrices', 'orderPriceMinTickSize',
            'oneWeekPriceChange', 'oneMonthPriceChange', 'lastTradePrice',
            'showGmpOutcome']

outcomes = '["Yes", "No"]'
outcomePrices = '["0.0015", "0.9985"]'
orderPriceMinTickSize = 0.001
oneWeekPriceChange = -0.001
oneMonthPriceChange = -0.001
lastTradePrice = 0.001
showGmpOutcome = False
```

## 결론

- **1주·1개월 변동은 Gamma 가 이미 계산해서 제공한다** (`oneWeekPriceChange`, `oneMonthPriceChange`). 부호 있는 절대 변동값으로 보인다(가격 스케일과 동일한 0~1 범위 단위).
- **1시간·1일(24시간) 변동 필드는 존재하지 않는다.** `oneDayPriceChange`·`oneHourPriceChange` 류의 키가 없다 — 검색 결과에 안 잡힘.
- `outcomes`·`outcomePrices` 는 JSON 문자열로 온다(파싱 필요), 기존 `_parse_string_array`/`_parse_float_array` 로 이미 처리 중인 패턴과 동일.

## 후속 구현에 필요한 계약

- `MarketSnapshotPayload`/`MarketSnapshot` 에 `price_change_1w`, `price_change_1mo` 필드 추가 시 `oneWeekPriceChange`·`oneMonthPriceChange` 를 그대로 캡처(재계산 없음).
- 1h/24h 는 이 API 로 못 받으므로 자체 `market_snapshot` 히스토리 조회로 계산해야 한다.

## 참고

- [ADR 2026-09-10: 확률 변동 정보 구간별 소싱 방식](decisions/2026-09-10-price-change-info-sourcing.md)
- `concenews-backend/src/modules/market/infrastructure/polymarket_client.py` — 기존 파싱 로직
