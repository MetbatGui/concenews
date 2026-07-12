# Spike: Polymarket API 탐구

**목표**: Market tracking slice에서 Polymarket API 사용 전략 수립
**기간**: 2026-07-09 ~ 2026-07-10
**상태**: 진행 중 (API 구조 파악 완료, 스키마 결정 중)

---

## 1. Polymarket API 구조

### 세 가지 공식 서비스

| API                 | 엔드포인트                       | 용도                     | 인증                              |
| ------------------- | -------------------------------- | ------------------------ | --------------------------------- |
| **Gamma API** | https://gamma-api.polymarket.com | 시장 메타데이터, 발견    | 불필요                            |
| **CLOB API**  | https://clob.polymarket.com      | 가격, 주문장, 거래       | 데이터 조회는 불필요, 주문은 필요 |
| **Data API**  | https://data-api.polymarket.com  | 사용자 포지션, 거래 이력 | 불필요                            |

**결정**: Gamma API + CLOB API 사용
**이유**: 가장 많은 필드 + 공식 지원 + 캐싱 가능

---

## 2. Market 데이터 구조

### 핵심 개념

**Market** = 이진 예측 이벤트 (e.g., "노르웨이가 2026 월드컵 우승할까?")

**Outcomes** = 가능한 결과

```json
outcomes: ["Yes", "No"]
```

**Outcome Prices** = 시장 확률 (consensus)

```json
outcomePrices: "[0.0585, 0.9415]"  ← JSON 문자열로 반환!
// Yes (우승): 5.85%
// No  (탈락): 94.15%
```

⚠️ **주의**: `outcomePrices`는 JSON 문자열이므로 `json.loads()` 필수

### GET /markets 응답 예제 (Norway FIFA 2026)

**요청:**

```bash
GET https://gamma-api.polymarket.com/markets?limit=100
```

**주요 필드:**

```python
{
    "id": "558951",
    "question": "Will Norway win the 2026 FIFA World Cup?",
    "conditionId": "0x7b52405ad0e0d31bfe970940b67d77f24ecedeab8a2361c11148c02a006e325c",
    "slug": "will-norway-win-the-2026-fifa-world-cup-893",
  
    # 결과 & 확률
    "outcomes": "[\"Yes\", \"No\"]",
    "outcomePrices": "[\"0.0585\", \"0.9415\"]",  # JSON 문자열
    "clobTokenIds": "[\"60447443...\", \"111538579...\"]",
  
    # 가격
    "lastTradePrice": 0.059,
    "bestBid": 0.058,
    "bestAsk": 0.059,
    "spread": 0.001,
  
    # 거래량 & 유동성
    "liquidityNum": 5184563.16722,
    "volumeNum": 124853572.75951944,
    "volume24hr": 4352554.247895972,
    "volume1wk": 32650001.282036085,
    "volume1mo": 88755805.1537155,
  
    # 시간
    "startDate": "2025-07-02T22:27:12.778Z",
    "endDate": "2026-07-20T00:00:00Z",
    "active": true,
    "closed": false,
  
    # 수수료
    "makerBaseFee": 1000,  # 0.1%
    "takerBaseFee": 1000,
  
    # 메타데이터
    "description": "...",
    "image": "https://...",
  
    # 참고: 나중에 거래할 때 필요
    "negRisk": true,
    "negRiskMarketID": "0x...",
}
```

---

## 3. 필드 분류

### Phase 1에서 저장 (필수)

```python
MarketSnapshot(
    market_id: str                  # id (식별)
    question: str                   # 설명
    outcomes: list[str]             # ["Yes", "No"]
    outcome_prices: list[float]     # [0.0585, 0.9415] (확률)
    last_price: float               # 최근 거래가 (신호용)
    best_bid: float
    best_ask: float
    spread: float                   # bid-ask 스프레드
    liquidity: float                # 유동성
    volume_24h: float               # 24시간 거래량
    timestamp: datetime             # 수집 시각
    end_date: datetime              # 마켓 종료
    active: bool
)
```

### 참고용 (저장하되 사용 안 함)

- `conditionId`: on-chain ID (blockchain 조회 시 필요 — phase 2+)
- `clobTokenIds`: ERC1155 토큰 주소 (거래 시 필요 — phase 2+)
- `negRisk`: 음수 위험 모드 (advanced — phase 2+)

### 무시

- `createdAt`, `updatedAt`: API 내부 메타
- `featured`, `archived`: UI 용
- `pagerDutyNotificationEnabled`: 운영 용

---

## 4. Price Change Tracking (Spike 감지)

### 개념

Market 가격이 급격하게 변하면 → 새로운 정보 신호
예: 뉴스 발표 후 5분 내 확률 10% 상승

### Phase 별 구현

| Phase                 | 작업                                             |
| --------------------- | ------------------------------------------------ |
| **1 (진행 중)** | 5분 주기로 MarketSnapshot 수집만                 |
| **2 (계획)**    | Spike detection: 이전 가격 vs 현재 가격 비교     |
| **3 (계획)**    | News-Market Matching: 뉴스 타임라인과 spike 연동 |

### Spike 감지 로직 (Phase 2)

```python
MarketSpike(
    market_id: str
    timestamp: datetime
    old_price: float
    new_price: float
    change_pct: float           # (new - old) / old * 100
    volume_24h: float           # 당시 거래량
    detected_at: datetime
)

def is_spike(old_price, new_price, threshold_pct=10):
    change = abs((new_price - old_price) / old_price * 100)
    return change > threshold_pct  # 10% 이상 변화
```

---

## 5. 데이터 소스 선택

### Top Markets by Volume (2026-07-10 기준)

**스포츠 (FIFA World Cup 2026):**

1. Norway: $124.8M
2. Belgium: $123.2M
3. Argentina: $122.1M
4. Switzerland: $121.4M
5. France: $108.6M
6. Spain: $98.8M
7. England: $91.8M

**정치:**
8. Oprah 2028 Democratic: $53.9M
9. LeBron 2028 Presidential: $53.4M
10. Bernie Sanders 2028: $51.1M

### Phase 1 마켓 선택

**선택**: Norway FIFA 2026 (ID: 558951)

**이유**:

- 거래량 충분 ($124.8M)
- 확률 명확 (Yes 5.85% = 매우 낮음)
- 실제 이벤트까지 시간 있음 (2026-07-20)
- 뉴스 연동 가능 (팀 소식, 부상 정보 등)

---

## 6. 알려진 제약사항

| 제약                             | 해결책                        |
| -------------------------------- | ----------------------------- |
| outcomePrices는 JSON 문자열      | `json.loads()` 후 파싱      |
| 가격은 인덱스 기반 (Yes=0, No=1) | outcomes 배열과 함께 저장     |
| API rate limit 명시 안 됨        | 보수적 5분 주기 (나중에 조정) |
| 실시간 가격이 필요한 경우        | WebSocket 사용 (phase 2+)     |

---

## 7. 다음 단계

### 즉시 (이번 세션)

- [ ] ADR: "Polymarket API 선택 + 데이터 수집 전략"
- [ ] spec-market-tracking.md 작성
- [ ] Alembic migration (market_snapshot, market_spike 테이블)

### 나중에 (Phase 2+)

- [ ] WebSocket 실시간 가격 수집
- [ ] Spike detection 로직
- [ ] News-Market matching
- [ ] 다른 거시경제 마켓 추가 (금리, 환율 등)

---

## 참고자료

- [Polymarket Docs](https://docs.polymarket.com/)
- [Gamma API Reference](https://docs.polymarket.com/developers/gamma-markets-api/get-markets)
- [Medium: Polymarket API Architecture](https://medium.com/@gwrx2005/the-polymarket-api-architecture-endpoints-and-use-cases-f1d88fa6c1bf)
- [AgentBets: Polymarket US API Guide](https://agentbets.ai/guides/polymarket-us-api-guide/)

---

## 8. Gamma vs CLOB vs Data API — 자세한 사용처

### Gamma API (Market Discovery)

| 엔드포인트            | 용도                      | 반환 데이터                                              | 사용 시기           |
| --------------------- | ------------------------- | -------------------------------------------------------- | ------------------- |
| `GET /markets`      | 마켓 목록 + 메타          | id, question, outcomes, outcomePrices, liquidity, volume | 마켓 발견, 스크리닝 |
| `GET /markets/{id}` | 단일 마켓 상세            | ↑ + description, image                                  | 마켓 상세 조회      |
| `GET /events`       | 이벤트 그룹               | event metadata, nested markets                           | 카테고리 찾기       |
| `GET /tags`         | 카테고리 필터             | tag list                                                 | 필터링              |
| `GET /series`       | 반복 이벤트 (주간 스포츠) | series metadata                                          | 시계열 마켓         |
| `GET /search`       | 키워드 검색               | 검색 결과                                                | 특정 마켓 찾기      |

**Phase 1 사용:**

```
Gamma: GET /markets?limit=100
  → 모든 마켓 조회
  → 로컬 필터: MACRO_KEYWORDS (태그가 고정 아님)
  → 저장: MarketSnapshot(id, question, prices, timestamp)
```

### CLOB API (Real-time Pricing)

| 엔드포인트                           | 용도          | 반환                     | 사용 시기           |
| ------------------------------------ | ------------- | ------------------------ | ------------------- |
| `GET /book?token_id=...`           | 주문장 스냅샷 | bids[], asks[], metadata | 유동성, spread 조회 |
| `GET /price?token_id=...&side=BUY` | 최고 호가     | price (한쪽만)           | 빠른 현재가         |
| `GET /midpoint?token_id=...`       | 중값          | midpoint                 | "공정한" 시장가     |
| `GET /spread?token_id=...`         | 호가 차       | bid, ask, spread_pct     | 유동성 평가         |
| `GET /price-history?...`           | 가격 히스토리 | [timestamp, price][]     | 차트, 변화 추적     |
| `POST /order`                      | 주문 생성     | order_id (인증 필요)     | 거래                |

**Phase 1 사용:** 선택적 (Gamma의 lastTradePrice로 충분, 필요시 추가)

**Phase 2 사용:** Spike detection에 필요

### Data API (Trader Intelligence)

| 엔드포인트                  | 용도           | 반환                                                             | 사용 시기                  |
| --------------------------- | -------------- | ---------------------------------------------------------------- | -------------------------- |
| `GET /holders?market=...` | 마켓별 탑 홀더 | proxyWallet, pseudonym, name, profileImage, amount, outcomeIndex | **탑 트레이더 추출** |
| `GET /positions?user=...` | 사용자 포지션  | conditionId, outcome, shares, unrealizedPnL                      | 개별 trader 포지션         |
| `GET /trades?user=...`    | 거래 이력      | timestamp, price, size, side, fees                               | 거래 패턴 분석             |
| `GET /activity?user=...`  | 사용자 활동    | timeline of actions                                              | 활동 추적                  |

**Phase 1 사용:** 선택적 (마켓 추적 후 Phase 2에서 trader tracking)

**Phase 2 사용:** Trader credibility 판별

---

## 9. Macro 필터링 전략

### Tag 문제

- Polymarket tags는 고정되지 않음
- 개발자가 임의로 추가 가능: "product market fit", "virgins", "Timothée Chalamet" 등
- 예: sports (FIFA, cricket), politics (Oprah, Bernie), meme (controversies, celebrities)

### 해결책: Keyword-based Filtering

```python
MACRO_KEYWORDS = [
  # 경제
  "federal", "interest rate", "inflation", "fed", "ecb", "boe",
  "gdp", "employment", "housing", "mortgage",
  
  # 정책
  "tariff", "trade", "regulation", "sanction",
  
  # 금융
  "crypto", "bitcoin", "ethereum", "altcoin", "etf", "stock",
  "dollar", "yen", "euro", "currency",
  
  # 거시 이벤트
  "recession", "crash", "bull market", "bear market",
  "merger", "acquisition", "ipo",
  
  # 지정학
  "war", "conflict", "ceasefire", "peace", "treaty",
  "russia", "ukraine", "china", "taiwan", "israel",
]

def is_macro(market_question: str) -> bool:
    q_lower = market_question.lower()
    return any(kw in q_lower for kw in MACRO_KEYWORDS)
```

**필터링 결과 (top 100 markets 기준):**

- ❌ 제외: "Norway FIFA", "Caitlin Clark", "Harvey Weinstein"
- ✅ 포함: "Fed raise rates", "Bitcoin $1M", "China invades Taiwan"

---

## 10. Phase별 API 사용 계획

### Phase 1: Market Snapshot (현재 진행)

```
Trigger: 5분 주기 scheduler
├─ Gamma: GET /markets?limit=100
├─ Filter: is_macro(question) = True
├─ Save: MarketSnapshot(id, question, prices, timestamp)
└─ Size: ~50-100개 macro 마켓
```

### Phase 2: Trader Tracking

```
Trigger: 마켓별 Snapshot 저장 후
├─ Data: GET /holders?market=conditionId&limit=20
├─ Extract: top 20 traders (pseudonym, profileImage, amount, position)
├─ Save: TraderSnapshot(market_id, trader_wallet, amount, side, timestamp)
└─ Detect: Anomaly (new account + large bet = 내부자 의심)
```

### Phase 3: News-Market-Trader Matching

```
Trigger: 뉴스 발생
├─ Find related markets (keyword match)
├─ Get price change + top traders
├─ Flag: "China policy news → Taiwan invasion market spike + whale bets No = insider?"
└─ Output: AnomalyAlert
```

---

**작성**: 2026-07-10 ~ 2026-07-11
**상태**: API 구조 완료, Phase 1 구현 준비 완료
