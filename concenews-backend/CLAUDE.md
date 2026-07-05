# concenews-backend CLAUDE.md

> 루트 [CLAUDE.md](../CLAUDE.md) 의 "언제 무엇을 볼까" 표에 상황별 문서 매핑 있음.
> 이 파일은 백엔드 특유 규칙만 담음.

## 코드 편집 후 필수 검증 (매번)

`src/` 또는 `tests/` 편집 후 **커밋 전** 반드시:

```bash
uv run ruff check src tests    # lint (문법, unused, style)
uv run ty check src            # 타입 검증
uv run pytest --ignore=spikes  # 테스트 (RED/GREEN 확인)
```

**모두 통과해야 커밋**. 실패 시 fix 우선.

- **ruff**: unused import, style, syntax 등 자동 catch (self-review 부담 감소)
- **ty**: 타입 오류 (Astral 신규 checker)
- **pytest**: TDD 검증

**범위**: 지금은 news 모듈만 (모듈 확장 시 대상 갱신).

---

## 설계 결정 순서 (ADR 강제)

**설계 결정이 트리거 매칭 시 코드 변경 전에 ADR 먼저**:

1. **Trigger 매칭 확인** ([adr-process.md](../../docs/adr-process.md) 표):
   - Domain 계약 (id/필드/invariant), 모듈 경계, 저장소 전략, 외부 dep, 원칙, 프로세스
2. **ADR 작성/갱신** (`docs/decisions/YYYY-MM-DD-{slug}.md`)
3. **Docs 갱신** (spec/plan/CLAUDE/convention) — ADR 링크 명시
4. **코드 변경 착수**

**예외 없음**. 유저가 "그냥 코드부터" 라 해도:
- "설계 trigger 매칭. ADR 먼저 작성. 승인?" **되물음**
- 승인 없이 trigger 관련 코드 착수 금지

**Superseded 처리**: 원 ADR 은 immutable. Status 만 갱신, 신규 파일 생성.

**금지**: 원 ADR 에 History 섹션 누적 (immutable 원칙 위반).

**위반 판정**: Trigger 매칭 결정을 대화만으로 확정 후 코드 착수. 세션 종료 시 손실 위험.

---

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
