# concenews-backend AGENTS.md

> 루트 [AGENTS.md](../AGENTS.md) 의 "언제 무엇을 볼까" 표에 상황별 문서 매핑 있음.
> 이 파일은 백엔드 특유 규칙만 담음.

## 코드 편집 후 필수 검증 (매번)

`src/` 또는 `tests/` 편집 후 **커밋 전** 반드시:

```bash
just check-branch-green
```

**모두 통과해야 커밋**. 실패 시 fix 우선.

하위 작업(ruff·ty·import-linter·unit·integration)은 리포 루트 `Justfile` 에 정의되어 있다. 목록은 `just --list`.

`check-e2e` 는 `check-branch-green` 에 **포함되지 않는다**. 실제 외부 API 상태에 의존하므로 병합 전 게이트가 아니라 배포 전 수동 실행한다.

---

## 코드 작성 전 필수 확인

- **[Modular Monolith](docs/architecture/modular-monolith.md)** — 폴더 구조 `src/modules/{context}/`, `public.py` 를 통한 계약 결합, import-linter 강제
- **[해당 기능의 Plan](docs/)** — `plan-{slice}.md` (예: [plan-news-fetch.md](docs/plan-news-fetch.md))
- **[Docstring](docs/conventions/docstring.md)** — Google Style. **필수 요약**:
  - 모든 함수/클래스/domain model 에 docstring
  - **Class (Pydantic 모델 포함)**: 첫 줄 요약 + 빈 줄 + 상세 + `Attributes:` 섹션
  - **함수**: `Args:` / `Returns:` / `Raises:` (해당 시)
  - **Test**: GWT 형식 (`Given:` / `When:` / `Then:`)
  - **코드 중간 주석 금지** — 네이밍으로 대체. WHY & 제약사항만 예외.

---

## Self-Review 체크리스트 (PR 병합 전)

- [ ] 모든 테스트 green (master green 규칙, 자세한건 [git-workflow.md](../docs/git-workflow.md))
- [ ] Diff 명확한가?
- [ ] 불필요한 코드 없나? (중복, 데드코드)
- [ ] 커밋 메시지 명확한가? (WHAT + WHY)
