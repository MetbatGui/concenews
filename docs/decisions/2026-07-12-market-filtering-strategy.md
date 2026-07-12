# ADR: 마켓 필터링 전략 — 화이트리스트 태그 + 키워드 2단계

**Status**: Accepted  
**Date**: 2026-07-12  
**Slice**: market-tracking

---

## Context

Polymarket 에서 수집한 마켓 중 거시경제(Macro) 마켓만 추출해야 함.
상위 200개 마켓 대부분이 스포츠/연예인(노이즈) → 필터링 필수.

**문제점**:
- Gamma `GET /markets?limit=100` 은 상위 거래량 순 반환 → macro markets 은 저순위
- 태그가 없는 경우도 있음 (확인 결과 상위 100개는 macro tags 0개)
- Keyword 만으로는 범위 애매 (예: OpenAI 태그는 50개 마켓, AI policy + 제품 뉴스 섞임)

Spike 완료: `spikes/polymarket-api/MACRO_TAGS.md` — 실제 tag ID 분류 (12개 macro, 20개 non-macro).

## Options Considered

### 필터 방식

| 옵션 | Pros | Cons |
|------|------|------|
| **A. 화이트리스트 태그 (Tag ID)** | 정확성 높음, 관리 용이 | 새 태그 추가 시 manual sync, 태그 부족한 마켓 놓침 |
| B. 키워드만 (question 검사) | 자동화, 새 시장 자동 수집 | 거짓양성 많음 (예: "interest rate hike" 농담글도 match) |
| C. LLM 분류 (질문 이해도 평가) | 정확성 최고 | API 비용, latency, 폴백 복잡도 |
| D. A + B (하이브리드) | 정확성 + 보전 | 구현 2단계, 유지보수 복잡도 |

### 태그 관리 방식

| 옵션 | Pros | Cons |
|------|------|------|
| **E. 하드코드 MACRO_TAG_IDS** | 단순, 성능 최고 | 새 macro 태그 추가 시 코드 변경 |
| F. DB table (tags config) | 런타임 동적 관리, 핫 리로드 | 복잡도, 불필요한 쿼리 |

### 블랙리스트 처리

| 옵션 | Pros | Cons |
|------|------|------|
| **G. 명시적 NON_MACRO_TAG_IDS** | 스포츠/연예인 확실히 제외 | 태그 수 증가 시 유지보수 |
| H. Blacklist 없음 (whitelist 만) | 간단 | 모호한 태그 실수로 포함 (예: Kansas = 지역 경제?) |

## Decision

**A + D + E + G**: 2단계 필터 (화이트리스트 태그 우선, 보전용 키워드), 하드코드 tag ID, 블랙리스트 명시.

### Step 1: Tag-based Filter (Primary)
```python
MACRO_TAG_IDS = {
  "933",      # federal-government
  "1396",     # international-affairs
  "101026",   # FDIC
  "833",      # ETF
  "101611",   # Altcoins
  "537",      # OpenAI (주의: 너무 넓음, 검증 필요)
  "777",      # maritime-transport
  "103482",   # COP
  "103357",   # Influenza
  "103269",   # Korea
  "101247",   # Macro-Graph
  "101250",   # Macro-Single
}

NON_MACRO_TAG_IDS = {
  # Sports
  "101025", "100626", "103813", "101104", "102076",
  # Entertainment & Celebrity
  "1512", "102136", "945", "101561", "100257", "101457", "104208", "104393",
  # Other (ambiguous)
  "790", "1571", "330", "101896", "100601", "101655", "100881", "104377",
  "713", "733", "101091", "100735", "101867",
}

# Logic
is_macro_tagged = any(tag_id in MACRO_TAG_IDS for tag_id in market_tags) and \
                  not any(tag_id in NON_MACRO_TAG_IDS for tag_id in market_tags)
```

### Step 2: Keyword Supplement (Fallback)
```python
MACRO_KEYWORDS = [
  "federal", "interest rate", "inflation", "fed", "ecb", "boe",
  "gdp", "employment", "housing", "mortgage", "recession",
  "tariff", "trade", "regulation", "sanction",
  "crypto", "bitcoin", "ethereum", "altcoin", "etf", "stock",
  "dollar", "yen", "euro", "currency",
  "bull market", "bear market", "merger", "acquisition", "ipo",
  "war", "conflict", "ceasefire", "peace", "treaty",
  "russia", "ukraine", "china", "taiwan", "israel",
]

is_macro_keyword = any(kw in market_question.lower() for kw in MACRO_KEYWORDS)
```

### Combined Logic
```python
def is_macro_market(market: Market) -> bool:
    # Priority 1: Explicit tag match
    if market.tags:
        is_tagged = any(t in MACRO_TAG_IDS for t in market.tags) and \
                    not any(t in NON_MACRO_TAG_IDS for t in market.tags)
        if is_tagged:
            return True
    
    # Priority 2: Fallback to keyword (preserve untagged macro markets)
    return is_macro_keyword(market.question)
```

## Rationale

### 2단계 필터 (Option D)

**Step 1: 태그 (정확성 우선)**:
- Polymarket 커뮤니티가 curate 한 태그 = 높은 신뢰도
- 실제 tag_id 분류 완료 (spike 기반) → 검증됨
- 거짓양성 최소화

**Step 2: 키워드 (보전 우선)**:
- 태그 없는 신규 macro 마켓 캡처 (예: "Fed rate decision" 방금 생성됨)
- 태그는 수집 후 추가되는 경우도 있음 (crowdsource)
- 키워드만으로는 노이즈 多, 태그로 먼저 필터한 후 키워드 사용 → 거짓양성 줄임

**LLM 제외 (Option C 배제)**:
- Phase 1 = MVP, 간단 필터로 시작
- 비용/latency 고려 시 overkill
- Phase 2 에서 "LLM 보정" 으로 정제 가능

### 하드코드 tag ID (Option E)

**이유**:
- tag ID 는 Polymarket 에서 변경 안 함 (불변)
- 초기 12개 macro + 15개 non-macro 충분히 관리 가능
- 성능 최적 (O(1) set membership check)

**유지보수 계획**:
- 분기마다 spike: `GET /tags` 조회 후 신규 태그 추가
- "새 매크로 태그 발견" → ADR 갱신 (status: Accepted, 코드 변경)

### 블랙리스트 명시 (Option G)

**이유**:
- "무엇을 제외하는가" 명확히 (스포츠/연예인/모호)
- 향후 태그 추가 시 어디에 분류할지 명확
- 예: "Kansas" 태그 발견 → "지역 경제 뉴스 가능" 판단 후 평가

## Reconsider When

### 정확도 부족
- **거짓음성 많음** (macro 마켓 놓침): 키워드 확장 or Phase 2 LLM 도입
- **거짓양성 많음** (노이즈 포함): 블랙리스트 확대 or LLM 검증

### 태그 품질 문제
- **태그가 부정확함**: 직접 Polymarket 커뮤니티 피드백, 또는 LLM 보정
- **새 매크로 태그 잦은 추가**: DB 기반 tag config 로 전환 (Option F)

### 성능 문제
- **API 호출 지연** (tag lookup 비용): 배치 조회 or 캐싱 (Redis)

### 범위 확대
- **다른 예측 시장 추가** (Kalshi, PredictIt): 각 플랫폼별 adapter, 필터 전략 검토

## Migration Path (미래)

### Phase 1 → Phase 2 (LLM 보정)
- 분류 신뢰도 점수 추가 (tag-based: 0.9, keyword-only: 0.6)
- LLM 검증: 낮은 신뢰도 마켓만 LLM 분류
- MarketSnapshot 에 `macro_confidence` 필드 추가
- 예상 churn: 2-3시간 (LLM API 호출, 필드 추가)

### DB 기반 태그 관리 (Rule of Three)
- 두 번째 모듈 (trader-tracking, sentiment analysis) 에서도 필터 필요할 시
- `tags_config` 테이블 신규 (tag_id, category, enabled)
- 런타임 로드, 핫 리로드 지원
- 예상 churn: 1-2시간 (table 생성, cache invalidation)

### Whitelist → Dynamic Learning
- Phase 3+ : 사용자 피드백 기반 automatic tag weighting
- 예: "이 태그는 실제로 거시경제 아님" 피드백 누적 → 가중치 조정

## References

- Spike Tag Classification: `concenews-backend/spikes/polymarket-api/MACRO_TAGS.md` — 실제 Tag ID 분류, 화이트리스트/블랙리스트 근거
- Spike Learnings: `concenews-backend/spikes/polymarket-api/LEARNINGS.md` — 마켓 구조, 필터링 목표
- Spec: `concenews-backend/docs/spec-market-tracking.md` (AC2 참고)
- 관련: [ADR 2026-07-12 polymarket-api-choice](./2026-07-12-polymarket-api-choice.md) (API 선택)
