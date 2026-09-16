# Kalshi API 계약 Spike: Learnings & Decision

> 관련 ADR: [2026-09-17 polymarket-to-kalshi-market-source-migration](../../../docs/decisions/2026-09-17-polymarket-to-kalshi-market-source-migration.md)

## Question

Kalshi 공개 시세 API로 `MarketSourcePort`를 구현할 수 있는가 — 인증 방식, 마켓/카테고리 스키마, "주요 마켓" 선정에 쓸 정렬·집계 수단을 확인한다.

## Candidates Evaluated

- `GET /markets` — 개별 마켓(예/아니오 계약) 목록
- `GET /events` — 마켓을 묶는 이벤트 단위
- `GET /series` — 이벤트를 묶는 시리즈(카테고리) 단위
- `GET /markets/trades` — 실거래 내역

## Findings

### 인증

- `/markets`, `/events`, `/series`, `/markets/trades` 전부 **인증 헤더 없이 200 OK**. 공개 read-only 엔드포인트.
- Base URL: `https://api.elections.kalshi.com/trade-api/v2` (OpenAPI 스펙엔 `external-api.kalshi.com`도 등재돼 있으나 실측은 `api.elections.kalshi.com`으로 정상 응답).
- Rate-limit 관련 응답 헤더(`X-RateLimit-*`, `Retry-After` 등)는 공개 엔드포인트 응답에 없음 — 인증 없는 상태에서 명시적 rate limit 신호는 확인 안 됨. 계속 폴링할 경우 보수적인 요청 간격을 직접 정해야 함.

### `category`/`series_ticker`는 Market 객체에 없다 — Event/Series 레벨 필드

가장 중요한 발견: **`Market` 스키마에는 `category`도 `series_ticker`도 없다.** 다음 계층에서만 존재한다.

| 레벨 | 카테고리 정보 |
|------|---------------|
| `Market` | 없음. `event_ticker`만 있음 |
| `Event` | `category`, `series_ticker` 있음 |
| `Series` | `category`(주 카테고리), `categories`(다중 카테고리 목록) 있음 |

즉 마켓의 카테고리를 알려면 `market.event_ticker` → `/events/{event_ticker}` (또는 `/events?event_ticker=...`) 조회로 한 단계 조인해야 한다. Polymarket의 tag 배열이 마켓 객체에 직접 붙어있던 것과 다른 구조다.

`Market` 실제 필드(OpenAPI `Market` 스키마, 2026-09-17 기준):
```
ticker, event_ticker, market_type, yes_sub_title, no_sub_title,
created_time, updated_time, open_time, close_time, latest_expiration_time,
status, notional_value_dollars,
yes_bid_dollars, yes_ask_dollars, no_bid_dollars, no_ask_dollars,
yes_bid_size_fp, yes_ask_size_fp, last_price_dollars,
previous_yes_bid_dollars, previous_yes_ask_dollars, previous_price_dollars,
volume_fp, volume_24h_fp, open_interest_fp, result, ...
```

### `_fp` 필드 = 고정소수점 문자열(스케일 곱 아님)

OpenAPI 공통 스키마:
- `FixedPointCount`: 계약 수량을 소수 2자리 **문자열**로 표현 (`"10.00"`). `volume_fp`, `volume_24h_fp`, `open_interest_fp` 등이 이 타입.
- `FixedPointDollars`: 가격을 소수점 달러 **문자열**로 표현 (`"0.5600"`).

즉 `volume_fp`는 `volume * 100` 같은 정수 스케일링이 아니라 **decimal string** — `float()`/`Decimal()` 파싱만 하면 된다. 실측 응답에서 값이 비어있는 마켓도 많음(막 생성된 auto-generated 스포츠 콤보 마켓 등, 거래 없음).

### 정렬 파라미터 — 공식으로 부재 확인

`GET /markets`의 쿼리 파라미터는 `limit, cursor, event_ticker, series_ticker, min/max_created_ts, min_updated_ts, min/max_close_ts, min/max_settled_ts, status, tickers, mve_filter` 뿐이다. **volume/popularity 기준 정렬 파라미터는 없다.** 실측으로도 `order_by=volume`을 붙여도 결과가 무시되고 동일하게 반환됨을 확인(OpenAPI 문서와 일치).

### "주요 마켓" 선정 — `/series?category=X&include_volume=true`가 실마리

`GET /series`는 `category` 필터와 `include_volume=true` 옵션을 제공한다. `include_volume=true`면 **시리즈별 누적 거래량**(`volume_fp`, 소수 문자열)을 함께 반환한다 — 실측(`category=Economics`, 873개 시리즈) 확인함:

```
KXCHIPBURRITO  Price of a Chipotle chicken burrito this month   volume_fp=99000.00
KXNVHOMEPRICE  Nevada House Price Index                          volume_fp=9889.00
KXPJMEMERGENCY PJM capacity emergency days                       volume_fp=98305.00
```

마켓 단위 정렬은 없지만, **시리즈 단위로는 거래량 기준 클라이언트 사이드 정렬이 가능**하다 — "이 카테고리에서 가장 활발한 시리즈부터" 식으로 우선순위를 매긴 뒤, 그 시리즈에 속한 이벤트/마켓을 내려받는 2단계 접근이 실현 가능하다. `/markets/trades?ticker=...`로 개별 마켓의 실거래 유무를 보조 신호로 쓸 수도 있다(거래 없는 자동 생성 마켓 걸러내기).

## Decision: 2단계(Series→Market) 조회 + 클라이언트 사이드 랭킹 채택

### Why

- Kalshi는 마켓 레벨 정렬·카테고리 필터를 제공하지 않지만, 시리즈 레벨에서는 `category` 필터 + `include_volume`으로 사실상 동등한 기능을 얻을 수 있다. 새 API를 자체 구현할 필요 없이 기존 엔드포인트 조합으로 해결된다.
- Polymarket 때처럼 개별 마켓 태그를 하나씩 조회하며 rate limit에 걸릴 위험이 원천적으로 없다 — `/series` 한 번 호출로 카테고리 전체의 집계 신호를 얻는다.

### Implementation Notes

- 카테고리 분류: `MarketClassifierService`는 이제 마켓 각각을 분류할 필요가 줄어든다. `/series?category=X`로 이미 분류된 시리즈 목록을 받고, 그 시리즈의 `event_ticker`로 이벤트를, 이벤트의 마켓들을 내려받으면 카테고리가 이미 붙어 있는 상태다. Polymarket용 태그 배치 분류 로직(`NEW_MARKETS_PER_CYCLE_LIMIT` 등)은 이 흐름엔 필요 없어질 가능성이 높다 — 실제 Slice 설계 시 재확인.
- "주요 마켓" 랭킹: 시리즈 `volume_fp` 내림차순 → 상위 N개 시리즈의 이벤트/마켓만 하위 조회. 완전한 마켓 단위 정렬은 아니지만 매크로/카테고리 우선순위 매기기엔 충분.
- `volume_fp`/`volume_24h_fp`는 decimal string이므로 `Decimal()`로 파싱. 정수 스케일 곱 불필요.
- 공개 엔드포인트에 명시적 rate limit 헤더가 없으므로, 폴링 주기는 보수적으로 직접 설정(예: 분당 수십 회 이내)하고 429 응답 발생 시 backoff를 별도로 검증해야 한다 — 이번 Spike 범위 밖.
- `event_ticker`로 이벤트 조회 시 `category`/`series_ticker`를 함께 받아오므로, 마켓→이벤트 조인은 이벤트를 캐싱해두면 N+1 호출을 피할 수 있다.

## 추가 조사: 참여자(지갑) 단위 공개 데이터 — 없음

`MarketParticipantSnapshotService`/`MarketParticipantObservationExclusion`([ADR 2026-08-15](../../../docs/decisions/2026-08-15-market-participant-observation-eligibility.md))은 Polymarket이 **온체인**이라 지갑별 보유·거래 내역이 공개된다는 전제 위에 서 있다.

Kalshi OpenAPI 전체를 훑은 결과, 포지션·주문·체결·잔고 관련 엔드포인트(`/portfolio/positions`, `/portfolio/orders`, `/portfolio/fills`, `/portfolio/balance` 등)는 전부 `portfolio` 태그이며 `KALSHI-ACCESS-KEY`/`KALSHI-ACCESS-SIGNATURE`(RSA-PSS 서명) 인증이 필요하고, **호출자 본인 계정 데이터만 반환한다**. 리더보드, 마켓별 보유자 목록, 타 트레이더 포지션 등 제3자 참여자 데이터를 노출하는 공개 엔드포인트는 존재하지 않는다.

**결론**: Kalshi는 KYC 기반 규제 거래소라 Polymarket과 달리 참여자 단위 공개 데이터가 구조적으로 없다. `market-participant` 모듈(스냅샷·관측 제외 등 참여자 추적 관련 기능 전체)은 Kalshi로 이식 불가능하다 — Market/News 매칭 계열 기능과 분리해서 별도로 결정해야 한다.

## References

- OpenAPI 스펙: `https://docs.kalshi.com/openapi.yaml` (2026-09-17 다운로드본으로 실측, title: "Kalshi Trade API Manual Endpoints", version 3.30.0)
- 실측: `GET /markets`, `GET /events`, `GET /series?category=Economics&include_volume=true`, `GET /markets/trades?ticker=...` 전부 한국 IP에서 200 OK 직접 확인 (2026-09-17)
