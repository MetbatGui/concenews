# concenews-backend CLAUDE.md

> 루트 [CLAUDE.md](../CLAUDE.md) 의 "언제 무엇을 볼까" 표에 상황별 문서 매핑 있음.
> 이 파일은 백엔드 특유 규칙만 담음.

## 코드 작성 순서 (TDD 강제)

**모든 프로덕션 코드는 실패하는 test 부터**:

1. **Red**: Test 작성 → 실패 확인 (ImportError, ValidationError 부재, 404 등)
2. **Green**: 최소 impl → test 통과
3. **Refactor**: 필요시 정리

**예외 없음**. 유저가 "일단 X 만들어봐" / "먼저 model 부터" 라 해도:
- "TDD 순서상 test 부터 작성하겠음. 승인?" **되물음**
- 승인 없이 `src/` 에 impl 파일 생성/편집 금지

**위반 판정**: 같은 slice 의 `tests/` 에 관련 test 없이 `src/` 프로덕션 파일 만듦.

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
