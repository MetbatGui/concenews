# concenews-backend AGENTS.md

> 루트 [AGENTS.md](../AGENTS.md) 의 "언제 무엇을 볼까" 표에 상황별 문서 매핑 있음.
> 이 파일은 백엔드 특유 규칙만 담음.

## 코드 편집 후 필수 검증 (매번)

`src/` 또는 `tests/` 편집 후 **커밋 전** 반드시:

```bash
just check-branch-green
```

`Justfile`의 하위 작업은 다음과 같다.

```bash
just check-ruff         # lint (문법, unused, style)
just check-ty           # 타입 검증
just check-imports      # 모듈 경계 검증
just check-unit         # 외부 의존성 없는 빠른 테스트
just check-integration  # 테스트용 PostgreSQL을 기동한 통합 테스트
just check-e2e          # 실제 외부 API + PostgreSQL 수동 검증 (토큰 필요)
```

**`check-branch-green`이 모두 통과해야 커밋**. 실패 시 fix 우선.
`check-e2e`는 외부 API 상태에 의존하므로 병합 전 게이트에 넣지 않고 배포 전 수동 실행한다.

- **ruff**: unused import, style, syntax 등 자동 catch (self-review 부담 감소)
- **ty**: 타입 오류 (Astral 신규 checker)
- **pytest**: TDD 검증

**범위**: 지금은 news 모듈만 (모듈 확장 시 대상 갱신).

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
