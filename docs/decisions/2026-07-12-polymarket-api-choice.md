# ADR: Polymarket API 선택 — Gamma + CLOB (Phase 1)

**Status**: Accepted  
**Date**: 2026-07-12  
**Slice**: market-tracking

---

## Context

Market-tracking slice 에서 Polymarket 에서 매크로경제 마켓 데이터 수집 필요.
Polymarket 은 3개의 공식 API 제공:

| API | 용도 | 인증 | 특징 |
|-----|------|------|------|
| **Gamma** | 마켓 메타 + 시가 | 불필요 | 발견/필터/기본정보 |
| **CLOB** | 가격/주문장/거래 | 불필요(조회) | 실시간 호가, 깊은 데이터 |
| **Data** | 사용자 포지션/거래 | 불필요 | 탑 트레이더, 거래 이력 |

Spike 완료: `spikes/polymarket-api/LEARNINGS.md`, `MACRO_TAGS.md`.

## Options Considered

### Phase 1 (마켓 스냅샷 수집)

| 옵션 | Pros | Cons |
|------|------|------|
| **A. Gamma only** | 단순, 가벼움 | 심화 분석 (spike/depth) 불가능 |
| **B. Gamma + CLOB** | 풀 마켓 정보 (가격/호가/유동성), 공식 지원 | CLOB 은 Phase 2+ 에서도 쓸 가능성 |
| C. Gamma + Data | 탑 트레이더 정보 | Phase 1 에는 불필요 (trader-tracking 은 Phase 2) |
| D. 모두 (Gamma+CLOB+Data) | 최대 데이터 | 오버스펙, 불필요한 API 호출, rate limit 부담 |

### Rate limit 전략

| 옵션 | Pros | Cons |
|------|------|------|
| **E. 보수 5분 주기** | Rate limit 여유, 안정성 | 실시간성 떨어짐 |
| F. 1분 주기 | 실시간성 | Rate limit 불명, 급변 시 실패 가능 |

### 캐싱 및 Dedup

| 옵션 | Pros | Cons |
|------|------|------|
| **G. 메모리 1차 + DB 2차** | 중복 방지, 빠름 | 리부팅 시 메모리 손실 |
| H. DB 만 (UPSERT) | 영속성 | 쿼리 비용 |

## Decision

**B + E + G**: Gamma + CLOB API, 5분 주기, 메모리/DB 2단계 dedup.

### Phase 1 (현재)
- **Gamma**: `GET /markets?limit=100` → 마켓 목록 + 메타 (question, outcomes, outcomePrices, liquidity, volume)
- **CLOB**: `GET /book?token_id=...` (필요시 추가 호가, 스프레드 확인) — 선택적
- **Rate limit**: 명시 없으니 보수적 5분 주기
- **Dedup**: 메모리 캐시(link) + DB unique constraint(market_id, timestamp)

### Phase 2 (예정)
- **CLOB**: `GET /price-history?token_id=...` → Spike detection (가격 히스토리)
- **Data**: `GET /holders?market=...` → 탑 트레이더 추출

### Phase 3 (예정)
- News-Market matching (Spike + news timeline)
- Trader anomaly detection

## Rationale

### Gamma + CLOB 선택 (Option B)

**Phase 1 필요 정보**:
- Market 메타: question, outcomes, outcomePrices → Gamma 충분
- 가격 신호: lastTradePrice, bestBid/Ask, spread → Gamma 충분, 필요시 CLOB 심화
- 유동성/거래량: liquidity, volume_24h → Gamma 포함

**Data API 제외 이유 (Option C 배제)**:
- Phase 1 = 마켓 추적만 (trader 데이터 불필요)
- Trader-tracking 은 Phase 2 별도 slice
- 불필요한 API 호출 = rate limit 낭비 + 복잡도

**Gamma only (Option A) 배제 이유**:
- CLOB 은 Phase 2+ 에서도 필수 (spike detection, real-time pricing)
- 지금 Gamma 기초 다지면 CLOB 추가는 minimal (token_id 매핑)
- 공식 지원, 장기 전략상 준비 이득

### 보수 5분 주기 (Option E)

**Rate limit 불명시**:
- 공식 문서 명확하지 않음 (APScheduler 같은 라이브러리의 기본값도 5분)
- 초기 배포 후 metrics 관찰 후 조정 가능 (ADR Reconsider When 참고)

**Dedup 2단계 (Option G)**:
- 메모리: tick 내 중복 ID skip (빠름)
- DB: 영속성 + unique constraint (race condition 방지)
- Redis 대체 준비: CachePort abstraction

## Reconsider When

### API 선택
- **Rate limit 실제 노출**: 초과 시 → API 스케줄링 라이브러리 (APScheduler) 도입 후 재검토
- **실시간성 필요**: 고주파 spike detection 필요 시 → WebSocket CLOB streaming (Phase 2+ 별도)
- **Trader 추적 시작**: Phase 2 시작 → Data API 추가, Market + Trader 동시 수집 검토

### 범위 확대
- **다중 스케줄러**: news (15분) + market (5분) + matching 등장 시 → APScheduler 로 통합 검토
- **고가용성**: 스케줄러 실패 대응 필요 시 → 별도 daemon 프로세스 (ADR 2026-07-06-scheduler-choice 참고)

## Migration Path (미래)

### Phase 1 → Phase 2 (Spike detection)
- CLOB `GET /price-history` 추가 (새 endpoint)
- MarketSnapshot 에 `old_price` 필드 추가
- MarketSpike 테이블 신규 (detection logic)
- 예상 churn: 2-3시간

### Phase 2 → Phase 3 (Trader tracking)
- Data API 호출 시작
- TraderSnapshot 테이블 신규
- 별도 스케줄러 또는 market tick 이후 즉시 실행
- 예상 churn: 4-5시간

### Polymarket API → 다른 예측 시장
- Port abstraction: `MarketSourcePort` (Gamma → alternative)
- 예: Kalshi, PredictIt 등 (future enhancement)
- 예상 churn: 6-8시간 (새 adapter + filtering 로직)

## References

- Spike LEARNINGS: `concenews-backend/spikes/polymarket-api/LEARNINGS.md` — API 구조 상세
- MACRO_TAGS: `concenews-backend/spikes/polymarket-api/MACRO_TAGS.md` — Tag classification
- Polymarket Docs: https://docs.polymarket.com/developers/gamma-markets-api/get-markets
- CLOB API Ref: https://docs.polymarket.com/developers/clob-api/get-orderbook
- Data API Ref: https://docs.polymarket.com/developers/data-api/get-holders
- 관련: [ADR 2026-07-06 scheduler-choice](./2026-07-06-scheduler-choice.md) (5분 주기 스케줄러)
- 관련: [ADR 2026-07-06 db-library](./2026-07-06-db-library.md) (PostgreSQL 저장)
