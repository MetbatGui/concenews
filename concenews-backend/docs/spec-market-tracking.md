# Spec: 매크로 마켓 분류

**버전**: 3.0
**작성일**: 2026-07-13
**상태**: Spike 완료, 설계 확정

---

## 사용자 스토리

**스토리**:
> 시스템이 Polymarket 에서 주기적으로 활성 마켓을 수집하여
> 매크로경제 관련 마켓과 노이즈(스포츠/연예인)를 자동 분류·저장한다.

**목표**: 이후 슬라이스(트래킹, 뉴스 연동)의 기반 데이터 구축

**Out of Scope** (별도 Spec):
- 마켓 스냅샷/가격 히스토리 수집 → `spec-market-snapshot.md` (작성 예정)
- Spike detection — Phase 2
- News-Market matching — Phase 3
- GET /markets API 엔드포인트 — 별도 slice

---

## Acceptance Criteria

### AC1. 백그라운드 스케줄러

- 앱 시작 시 스케줄러 등록 (FastAPI lifespan)
- 주기: 매 5분
- 실행: 마켓 fetch → 신규 분류 → DB 저장

### AC2. 마켓 Fetch

```
GET https://gamma-api.polymarket.com/markets
  limit=100
  active=true
  order=volume24hr
  ascending=false
```

- 5페이지 × 100개 = 최대 500개 수집
- `volume24hr` 내림차순: 현재 거래 활발한 마켓 우선
- `active=true`: 활성 마켓만

### AC3. 분류 캐시 조회 (DB)

```sql
SELECT condition_id FROM market_classification
WHERE end_date > NOW()
```

- 이미 분류된 마켓 → 태그 조회 스킵
- `end_date` 지난 마켓 → 자동 만료 (별도 삭제 job 불필요)
- `active` 재확인 없음 (end_date 기준으로 충분)

### AC4. 신규 마켓 태그 조회 — 비동기 병렬

```
GET https://gamma-api.polymarket.com/markets/{condition_id}/tags
```

- 캐시 미스 마켓만 대상
- asyncio.gather 병렬 실행
- 실측: 50콜 = 0.61초, 레이트리밋 없음
- Gamma API 레이트리밋: 4,000 req/10s

### AC5. 분류 로직

```python
def classify(tag_ids: set[int]) -> str:
    if tag_ids & NON_MACRO_IDS:
        return "NON_MACRO"   # 블랙리스트 우선
    if tag_ids & MACRO_IDS:
        return "MACRO"
    return "UNKNOWN"         # MACRO 없음 → 제외
```

**NON_MACRO_IDS (블랙리스트, 엄격)**

스포츠:
```
1 (Sports), 100350 (Soccer), 102232 (FIFA World Cup), 102350 (2026 FIFA World Cup),
105315 (Tournament Futures), 100219 (Golf), 102112 (PGA TOUR), 102446 (The Masters),
104278 (invitational), 104279 (augusta)
```

엔터테인먼트:
```
53 (Movies), 18 (Awards), 596 (Culture/pop-culture), 102109 (GTA VI)
```

개인/사건:
```
756 (Epstein), 102424 (Maxwell), 102429 (Ghislaine Maxwell),
105562 (Graham Platner), 105151 (James Talarico), 105150 (Ken Paxton),
1104 (bernie sanders)
```

**MACRO_IDS (화이트리스트, 넓게)**

경제/금융:
```
120 (Finance), 100328 (Economy), 101800 (Economic Policy),
159 (Fed), 100196 (Fed Rates), 101550 (Jerome Powell),
105160 (Fiscal), 100207 (Taxes),
102599 (IPO), 600 (IPOs), 102859 (Token Sales),
1312 (Crypto Prices), 105297 (Crypto Listings), 105292 (Crypto Legal)
```

크립토:
```
21 (Crypto), 235 (Bitcoin), 102785 (Metamask), 102784 (Consensys),
136 (Airdrops), 336 (token launch)
```

지정학:
```
100265 (Geopolitics), 101253 (Macro Geopolitics), 101794 (Foreign Policy),
366 (world affairs), 103027 (Ukraine Peace Deal),
96 (Ukraine), 303 (China), 95 (Russia), 180 (Israel), 78 (Iran),
192 (NATO), 154 (Middle East), 166 (South Korea), 101270 (Turkey)
```

기술/AI:
```
439 (AI), 835 (artificial intelligence), 662 (llm),
1401 (Tech), 101999 (Big Tech), 537 (OpenAI)
```

정치 (넓게 포함):
```
2 (Politics), 144 (Elections), 1101 (US Election),
1597 (Global Elections), 101206 (World Elections),
126 (Trump), 101191 (Trump Presidency), 102886 (President),
514 (Congress), 100199 (Senate), 264 (Primaries), 102670 (California Governor)
```

내부 운영 태그 (분류 무시):
```
100215 (All), 102458 (Earn 4%), 102169 (Hide From New),
103715 (HFC), 101252 (Macro Election 2), 103149/103151/104182 (Rewards *)
```

### AC6. 분류 결과 저장 (market_classification 테이블)

```sql
CREATE TABLE market_classification (
    condition_id   TEXT PRIMARY KEY,
    question       TEXT NOT NULL,
    classification TEXT NOT NULL,   -- 'MACRO' | 'NON_MACRO'
    tags_json      JSONB,
    end_date       TIMESTAMPTZ NOT NULL,
    classified_at  TIMESTAMPTZ NOT NULL
);
```

- MACRO, NON_MACRO 모두 저장 (UNKNOWN 제외 — 저장 불필요)
- `end_date` = Gamma API 응답의 `endDateIso`
- `classified_at` = 분류 시각

### AC7. 에러 처리

- API timeout / 404 → 로그 + skip (다음 tick 재시도)
- 태그 조회 실패 → UNKNOWN 처리 → skip (저장 안 함)
- DB 실패 → 로그
- 개별 마켓 실패 → 다른 마켓 계속 진행 (부분 성공)

---

## 전체 흐름

```
[스케줄러 tick — 매 5분]
  ↓
DB: SELECT condition_id WHERE end_date > NOW()  (캐시 로드)
  ↓
Gamma API: GET /markets × 5 페이지  (500개)
  ↓
신규 = 500 IDs - 캐시 IDs
  ↓
asyncio.gather: GET /tags × 신규 수  (병렬)
  ↓
classify(tag_ids) → MACRO | NON_MACRO | UNKNOWN
  ↓
MACRO, NON_MACRO → INSERT market_classification
UNKNOWN → skip
```

---

## 기술 결정

| 항목 | 결정 | 근거 |
|------|------|------|
| API | Gamma API | [ADR 2026-07-12](../../docs/decisions/2026-07-12-polymarket-api-choice.md) |
| 필터 전략 | 블랙리스트 우선 → 화이트리스트 | [ADR 2026-07-12](../../docs/decisions/2026-07-12-market-filtering-strategy.md) |
| DB | SQLAlchemy 2.0 + psycopg + PostgreSQL | [ADR 2026-07-06](../../docs/decisions/2026-07-06-db-library.md) |
| Scheduler | asyncio + FastAPI lifespan | [ADR 2026-07-06](../../docs/decisions/2026-07-06-scheduler-choice.md) |
| 시간대 | TIMESTAMPTZ (UTC 저장) | [ADR 2026-07-05](../../docs/decisions/2026-07-05-timezone-policy.md) |
| 태그 캐시 | DB 기반, end_date 만료 | Spike 실측 |
| 태그 병렬 조회 | asyncio.gather | Spike 실측: 50콜/0.61초, 레이트리밋 없음 |

---

## 참고

- **Spike LEARNINGS**: `spikes/polymarket-tags/LEARNINGS.md`
- **Spike 스크립트**: `spikes/polymarket-tags/`
- **Spike 결과 JSON**: `spikes/polymarket-tags/results/`
