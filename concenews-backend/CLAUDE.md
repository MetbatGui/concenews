# concenews-backend CLAUDE.md

## 설계 원칙 (참고)

모든 백엔드 설계는 루트 CLAUDE.md의 원칙을 따름:

### 아키텍처 & 프로세스
- **[DDD](../docs/architecture/principles/ddd.md)** — 4계층 (Endpoint, Service, Domain, Repository)
- **[XP](../docs/architecture/principles/xp.md)** — TDD (Red-Green-Refactor), Refactoring, Simple Design
- **[Vertical Slices](../docs/architecture/principles/vertical-slices.md)** — Spike → Spec → Plan → Integration Test → Unit Test

### Git & GitHub
- **[Git Workflow](../docs/git-workflow.md)** — feature/{slice} 브랜치, 명확한 커밋
- **[GitHub Strategy](../docs/github-strategy.md)** — Milestone (Slice), Epic Issue (Plan 후), PR automation

---

## 모듈러 모놀리스 구조

각 Slice는 **독립적인 모듈**:

```
modules/
  ├─ news_fetch/
  │  ├─ endpoints.py     (FastAPI route)
  │  ├─ services.py      (Business logic)
  │  ├─ domain.py        (Domain model, Pydantic)
  │  └─ repositories.py   (Data access)
  ├─ market_info/
  │  ├─ endpoints.py
  │  ├─ services.py
  │  ├─ domain.py
  │  └─ repositories.py
  └─ matching/
     ├─ endpoints.py
     ├─ services.py
     ├─ domain.py
     └─ repositories.py
```

### 역할 분명:
- **Endpoint**: HTTP 변환만 (Request/Response → DTO)
- **Service**: 비즈니스 로직 (외부 API, 조합 로직)
- **Domain**: 도메인 규칙 (검증, 계산, 불변성)
- **Repository**: 데이터 접근 (저장소 추상화)

---

## TDD 순서 & PR 단위 (모든 Slice)

### PR 구성 (예: news-fetch)

```
PR #1: Test: Integration test (RED)
  └─ GET /endpoint 스펙 정의

PR #2: Feat: Domain
  └─ NewsItem 모델 + 검증

PR #3: Feat: Repository
  └─ 데이터 접근 계층

PR #4: Feat: Service
  └─ 비즈니스 로직

PR #5: Feat: Endpoint (GREEN)
  └─ HTTP 변환, 모든 테스트 통과

PR #6: Refactor: 코드 정리
  └─ 복잡도 제거, 네이밍 개선

PR #7: Closes #{issue}
  └─ 마지막 PR, Issue 자동 close
```

### 각 PR 규칙
- 1 PR = 1 단위 기능 또는 1 리팩터 (focused)
- Self-review 체크리스트 통과
- "Related to #{issue}" (마지막 제외)
- "Closes #{issue}" (마지막만)

---

## 커밋 컨벤션 (루트 CLAUDE.md 참고)

```
✨feat: NewsRepository 구현

NewsAPI에서 뉴스를 fetch하고 저장하는 로직.
Integration Test: test_get_news_returns_articles
```

---

## Self-Review 체크리스트

PR 병합 전:

- [ ] 모든 테스트 green (Integration + Unit)
- [ ] Diff 명확한가? (한눈에 의도가 보이나)
- [ ] 불필요한 코드 없나? (중복, 데드코드)
- [ ] 리팩터링 필요? (복잡도, 네이밍)
- [ ] 커밋 메시지 명확한가? (WHAT + WHY)
