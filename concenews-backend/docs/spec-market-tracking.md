# Spec: 마켓 추적 기능

## 사용자 스토리

**주요 사용자**: 트레이더, 투자자, 매크로 경제 이벤트 추적자
(직접 소비자는 향후 GET /markets 사용자 — 이 slice 는 추적 저장소 구축)

**스토리**:
> 시스템이 Polymarket 에서 주기적으로 매크로경제 마켓 정보를 수집하여 저장한다.
> 각 마켓의 가격, 유동성, 거래량 변화를 추적한다.
> 급격한 가격 변화(spike)를 감지하여 뉴스와 연동한다.

**목표**: 
- 매크로경제 마켓 vs 노이즈(스포츠/연예인) 자동 분류
- 시간 경과에 따른 마켓 스냅샷 수집 (히스토리 보존)
- Phase 2: Spike detection (가격 급변 감지)
- Phase 3: News-Market matching (뉴스와 가격변화 연동)

---

## Acceptance Criteria

### AC1. 백그라운드 스케줄러 (5분 주기)
- 앱 시작 시 스케줄러 등록
- 주기: 매 5분
- 실행: Polymarket Gamma API 로 마켓 데이터 fetch

### AC2. 매크로경제 마켓 필터링 (2단계)

#### Step 1: 태그 필터 (화이트리스트 + 블랙리스트)
- Gamma GET /markets?limit=100 호출
- 각 마켓별 태그 조회: GET /markets/{id}/tags (또는 일괄 후처리)
- 화이트리스트 태그 매칭: MACRO_TAG_IDS 포함 시 포함
- 블랙리스트 태그 매칭: NON_MACRO_TAG_IDS 포함 시 제외

**MACRO_TAG_IDS (최소 12개)**:
```
933 (federal-government), 1396 (international-affairs), 101026 (FDIC),
833 (ETF), 101611 (Altcoins), 537 (OpenAI), 777 (maritime-transport),
103482 (COP), 103357 (Influenza), 103269 (Korea),
101247 (Macro-Graph), 101250 (Macro-Single)
```

**NON_MACRO_TAG_IDS (최소 15개)**:
```
Sports: 101025, 100626, 103813, 101104, 102076
Entertainment/Celebrity: 1512, 102136, 945, 101561, 100257, 101457, 104208, 104393
Other: 790, 1571, 330, ...
```

#### Step 2: 키워드 필터 (보조, 태그 부족 시)
```python
MACRO_KEYWORDS = [
  # 경제
  "federal", "interest rate", "inflation", "fed", "ecb", "boe",
  "gdp", "employment", "housing", "mortgage", "recession",
  
  # 정책
  "tariff", "trade", "regulation", "sanction",
  
  # 금융
  "crypto", "bitcoin", "ethereum", "altcoin", "etf", "stock",
  "dollar", "yen", "euro", "currency",
  
  # 거시 이벤트
  "bull market", "bear market", "merger", "acquisition", "ipo",
  
  # 지정학
  "war", "conflict", "ceasefire", "peace", "treaty",
  "russia", "ukraine", "china", "taiwan", "israel",
]
```

### AC3. 마켓 스냅샷 저장
- PostgreSQL 저장 (persist)
- Table: `market_snapshot`
- Fields:
  ```
  market_id: str (Polymarket ID, 식별자)
  question: str (마켓 설명, 예: "Will Norway win 2026 FIFA World Cup?")
  outcomes: list[str] (["Yes", "No"])
  outcome_prices: list[float] (확률, 예: [0.0585, 0.9415])
  last_price: float (최근 거래가)
  best_bid: float
  best_ask: float
  spread: float (bid-ask gap)
  liquidity: float (유동성)
  volume_24h: float (24시간 거래량)
  volume_1w: float (1주일)
  volume_1m: float (1개월)
  end_date: datetime (마켓 종료일, KST)
  active: bool (현재 활성 여부)
  closed: bool (종료 여부)
  timestamp: datetime (수집 시각, KST)
  
  (참고: conditionId, clobTokenIds 는 저장하되 Phase 2+ 에서 사용)
  ```

- Unique constraint: (market_id, timestamp) — 같은 마켓의 시간대별 스냅샷
- Index: (market_id, timestamp DESC) 고속 조회

### AC4. Fetch & Save 흐름
```
Scheduler tick (5분 마다)
   ↓
Gamma: GET /markets?limit=100
   ↓
Each market:
   ├─ GET /markets/{id}/tags (태그 조회)
   ├─ Filter: is_macro_tagged(tags)? + is_macro_keyword(question)?
   │   ├─ No → skip
   │   └─ Yes → 계속
   ├─ Adapter: raw dict → MarketSnapshot
   ├─ Dedup: market_id 최근 스냅샷과 가격 비교
   │   ├─ 동일하면 (cache hit) → skip
   │   └─ 변경 시 → DB insert
   └─ Persist: MarketSnapshot save
```

### AC5. Dedup 전략
- **1차 (메모리)**: 같은 tick 내 중복 ID skip
- **2차 (DB)**: 마켓 ID 의 최근 스냅샷 과 현재 가격 비교
  - 동일 가격 → skip (의미 있는 변화 없음)
  - 변경 → insert (히스토리 보존)

### AC6. 에러 처리
- 외부 API 실패 (timeout, 404) → 로그 + skip (다음 tick 재시도)
- 태그 조회 실패 → 키워드 필터만 사용
- DB 실패 → 로그
- 개별 마켓 실패 → 다른 마켓 진행 (부분 성공)

### AC7. GET /markets 아직 없음
- Phase 1: Collector 만 구축 (백그라운드)
- Phase 2+: GET /markets 조회 endpoint (별도 slice)

---

## Out of Scope

- 실시간 WebSocket 가격 (Phase 2+)
- Spike detection (급격한 변화 감지) — Phase 2
- News-Market matching — Phase 3
- 사용자별 알림
- 트레이더 정보 (Phase 2 시작)
- 체인 데이터 (on-chain 거래, negRisk, token transfers)

---

## 기술 결정 (Spike 후 확정 예정)

### API 선택
- **Gamma API** (`https://gamma-api.polymarket.com`) + **CLOB API**
  - 용도: 마켓 메타데이터, 시가, 호가 정보
  - 인증: 불필요
  - Rate limit: 명시 없음 (보수적 5분 주기로 시작)
  - 결정근거: [ADR 2026-07-12 polymarket-api-choice](../../docs/decisions/2026-07-12-polymarket-api-choice.md)

### DB
- SQLAlchemy 2.0 sync + psycopg
- PostgreSQL 17
- Alembic migration (`market_snapshot` 테이블)
- 상세: [ADR 2026-07-06 db-library](../../docs/decisions/2026-07-06-db-library.md)

### Scheduler
- stdlib `asyncio` (FastAPI lifespan 통합)
- 또는 APScheduler (필요시)
- 결정근거: [ADR 2026-07-06 scheduler-choice](../../docs/decisions/2026-07-06-scheduler-choice.md)

### 마켓 필터
- 태그 + 키워드 2단계 필터 (화이트리스트 → 키워드 fallback)
- Tag 화이트리스트/블랙리스트 유지보수
- 향후 LLM 보정 가능 (Phase 2+)
- 결정근거: [ADR 2026-07-12 market-filtering-strategy](../../docs/decisions/2026-07-12-market-filtering-strategy.md)

### 시간대
- 모든 datetime: KST (Asia/Seoul, UTC+9)
- DB 저장: TIMESTAMPTZ (timezone aware)
- Adapter: API (UTC) → KST 변환
- 상세: [ADR 2026-07-05 timezone-policy](../../docs/decisions/2026-07-05-timezone-policy.md)

---

## 구현 상태

1. ✅ **Spike 완료** (`spikes/polymarket-api/LEARNINGS.md`, `MACRO_TAGS.md`)
2. → **Spec** (현재 문서)
3. → **ADR 작성** (API 선택, 필터 전략)
4. → **Plan** 작성
5. → **Issue** 생성 (Epic)
6. → **Implementation** (TDD: PR #1-7 expected)

---

## 참고자료

- **Spike 문서**: `spikes/polymarket-api/LEARNINGS.md` — API 구조, Phase 별 계획
- **Tag 분류**: `spikes/polymarket-api/MACRO_TAGS.md` — 실제 Tag ID 와 필터 규칙
- **Plan 문서** (작성 예정): `plan-market-tracking.md` — TDD 순서, PR 분리, 폴더 구조
- **Polymarket 공식 문서**: https://docs.polymarket.com/
- **Gamma API Reference**: https://docs.polymarket.com/developers/gamma-markets-api/get-markets

---

**버전**: 1.0  
**작성일**: 2026-07-12  
**상태**: 설계 완료 (ADR 작성 대기)
