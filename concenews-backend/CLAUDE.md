# concenews-backend CLAUDE.md

## 코드 작성 전 필수 확인

- **[Modular Monolith](docs/architecture/modular-monolith.md)** — 폴더 구조, 모듈 경계
- **해당 기능의 Plan** — 구체적 설계 (예: [plan-news-fetch.md](docs/plan-news-fetch.md))

---

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

**[docs/architecture/modular-monolith.md](docs/architecture/modular-monolith.md) 참고**

- 폴더 구조: `src/modules/{context}/`
- 모듈 경계: `public.py`를 통한 계약 결합만 허용
- import-linter로 강제

---

## TDD & PR 전략

각 Slice의 Plan 문서 참고 ([예: plan-news-fetch.md](docs/plan-news-fetch.md))

## Spike Process

[Spike 프로세스](docs/spike-process.md) 참고 (기술 검증 → LEARNINGS.md → 삭제)

## Docstring & 코드 스타일

[Google Style Docstring Convention](docs/conventions/docstring.md) 참고

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
