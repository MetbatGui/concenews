# concenews-backend CLAUDE.md

> 루트 [CLAUDE.md](../CLAUDE.md) 의 "언제 무엇을 볼까" 표에 상황별 문서 매핑 있음.
> 이 파일은 백엔드 특유 규칙만 담음.

## 코드 작성 전 필수 확인

- **[Modular Monolith](docs/architecture/modular-monolith.md)** — 폴더 구조 `src/modules/{context}/`, `public.py` 를 통한 계약 결합, import-linter 강제
- **[해당 기능의 Plan](docs/)** — `plan-{slice}.md` (예: [plan-news-fetch.md](docs/plan-news-fetch.md))
- **[Docstring](docs/conventions/docstring.md)** — Google style

---

## Self-Review 체크리스트 (PR 병합 전)

- [ ] 모든 테스트 green (master green 규칙, 자세한건 [git-workflow.md](../docs/git-workflow.md))
- [ ] Diff 명확한가?
- [ ] 불필요한 코드 없나? (중복, 데드코드)
- [ ] 커밋 메시지 명확한가? (WHAT + WHY)
