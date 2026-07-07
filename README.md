# Concenews

**개인 거시경제 투자자를 위한 뉴스-예측시장 실시간 분석 플랫폼**

---

## 배경

거시경제 뉴스는 공식 채널에서 충분히 다루지만,  
**예측시장(Polymarket)은 뉴스의 선행 신호를 포함**:

- 시장 전문가의 내재 예상
- 언론이 놓친 거시 이벤트
- 급격한 확률 변화 = 새로운 정보

→ 뉴스 + 시장 신호를 함께 보면 **투자 신호 더 선명**

---

## 주요 기능

### 1. 뉴스 수집 & 분석
- Macro news 자동 수집 (Fed, 인플레이션, GDP 등)
- 키워드 자동 생성 (TFIDF / AI)
- 중복 제거 캐시

### 2. 폴리마켓 실시간 추적
- 5분 주기 시장 데이터 수집
- 거래량/유동성/가격 추적
- 확률 급변 감지 (이상 신호)

### 3. News ↔ Market 연동
- 뉴스 키워드 + 시장 변화 매칭
- "이 뉴스가 어떤 시장을 움직였나?" 추적
- 배치 처리 (1시간 주기)

### 4. 신호 대시보드
- 신규 뉴스 + 관련 시장 확률
- 확률 급변 & 관련 뉴스 타임라인

---

## 아키텍처

```
┌─ News Module
│  ├─ Collection (TheNewsAPI)
│  ├─ Storage (PostgreSQL)
│  └─ Enrichment (키워드 생성)
│
├─ Market Module  
│  ├─ Tracker (Polymarket API)
│  ├─ Storage (PostgreSQL)
│  ├─ Anomaly Detector (이상 거래)
│  └─ Matcher (News ↔ Market)
│
└─ API Layer
   ├─ GET /news (+ 관련 시장)
   └─ GET /insights (이상 신호 + 뉴스)
```

---

## 기술 스택

- **Backend**: Python 3.13 + FastAPI
- **DB**: PostgreSQL + Alembic (schema management)
- **수집**: Asyncio Scheduler (백그라운드)
- **분석**: TFIDF + AI (Phase 2)
- **테스트**: Pytest (Unit + Integration + System)

---

## 개발 진행

### ✅ 완료
- [x] News Collection (news-fetch) — [PR #12](https://github.com/MetbatGui/concenews/pull/12)
- [x] NewsCollectorService (news-collection) — [PR #20-22](https://github.com/MetbatGui/concenews/pull/22)
- [x] Bootstrap DI + Lifespan

### 🔄 진행 중
- [ ] Market Tracking (Polymarket)
- [ ] News-Market Matching

### 📋 예정
- [ ] Anomaly Detection
- [ ] Web Dashboard

---

## ⚠️ 면책

- **후행 데이터**: 뉴스·시장 데이터는 수 시간~5분 시차
- **수익 보장 없음**: 시장 신호 ≠ 수익
- **정보 분석만**: 투자 조언 아님
- **자체 판단 책임**: 손실 책임 없음

---

## 빠른 시작

### 요구사항
- Python 3.13+
- PostgreSQL 15+
- TheNewsAPI token (https://thenewsapi.com)
- Polymarket API access (https://polymarket.com/api)

### 설정
```bash
cd concenews-backend
uv sync

# .env 생성 (template: .env.example)
cp .env.example .env
# API 키 입력

# Alembic 마이그레이션
uv run alembic upgrade head

# 테스트
uv run pytest tests/ -v

# 개발 서버
uv run python -m uvicorn src.main:app --reload
```

---

## 문서

### 개발 가이드
- [Vertical Slice 개발 흐름](docs/architecture/principles/vertical-slices.md)
- [GitHub 관리 규칙](docs/github-strategy.md)
- [테스트 전략](concenews-backend/docs/conventions/testing.md)

### 설계 결정
- [ADR Index](docs/decisions/README.md)
- [Spike-Learning-Spec 정밀도](docs/decisions/2026-07-07-spike-learning-spec-fidelity.md)
- [Bootstrap DI 전략](docs/decisions/2026-07-07-di-bootstrap-strategy.md)

### 명세
- [News Collection Spec](concenews-backend/docs/spec-news-collection.md)
- [News Fetch Spec](concenews-backend/docs/spec-news-fetch.md)

---

## 라이선스

**Personal Use Only**  
상업적 사용 금지. 개인 투자 목적만 허용.

---

## 문의

Issues & Discussions 활용.

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
