# AGENTS.md

## 지식 저장 정책

**모든 학습/규칙/결정은 프로젝트 문서에 기록. 에이전트 로컬 메모리 사용 금지.**

- 새 규칙/피드백 → `AGENTS.md` 또는 `docs/` 해당 문서에 직접 반영
- 설계 결정 → ADR (`docs/decisions/`)
- Codex/Claude 공통 SSOT = 리포 내 마크다운
- **이 파일이 SSOT.** `CLAUDE.md` 는 이 파일을 가리키는 포인터일 뿐 — 내용 복사/이전 금지
- 에이전트 전용 설정(skill, hook, MCP)은 `.claude/` · `.codex/` 등 각자 위치에. 지침 파일에 중복 금지
- **Why:** SSOT 단일화, 에이전트 간 이식성, drift 방지, git 이력 추적

---

## 언어 정책 (필수)

**모든 산출물 한국어 작성**:

- Docstring, 커밋 메시지, 문서, 대화, 코드 리뷰, 주석 모두 한국어
- 예외: 코드 식별자 (변수/함수/클래스명) 는 영어
- 사용자가 명시적으로 요청하지 않는 한 영어 사용 금지

**Why:** 사용자 모국어. 업무 효율.

---

## 커밋 컨벤션

```
{GITMOJI}{type}: {title}

{description}          ← 필수
- {detail}             ← 선택 (복잡한 작업만)
```

gitmoji는 type에 붙여 쓴다: `✨feat` `🐛fix` `♻️refactor` `📝docs` `🧪test` `🔧chore`

상세 규칙·예시: [git-workflow.md § Commit 메시지](docs/git-workflow.md)

---

## 설계 결정 순서 (ADR 강제)

**설계 결정이 트리거 매칭 시 코드·문서 변경 전에 ADR 먼저**:

1. **Trigger 매칭 확인** ([adr-process.md](docs/adr-process.md) 표):
   - Domain 계약 (id/필드/invariant), 모듈 경계, 저장소 전략, 외부 dep, 원칙, 프로세스
2. **ADR 작성/갱신** (`docs/decisions/YYYY-MM-DD-{slug}.md`) + 인덱스 갱신
3. **Docs 갱신** (spec/plan/AGENTS/convention) — ADR 링크 명시
4. **변경 착수**

**예외 없음**. 유저가 "그냥 코드부터" 라 해도:
- "설계 trigger 매칭. ADR 먼저 작성. 승인?" **되물음**
- 승인 없이 trigger 관련 착수 금지

**위반 판정**: Trigger 매칭 결정을 대화만으로 확정 후 착수. 세션 종료 시 손실 위험.

ADR 형식·Superseded 처리·immutable 원칙은 [adr-process.md](docs/adr-process.md).

**적용 범위**: 계층 무관 ([ADR 2026-08-14](docs/decisions/2026-08-14-cross-cutting-rule-placement.md)).

---

## 코드 작성 순서 (TDD 강제)

**모든 프로덕션 코드는 실패하는 test 부터.**
Red-Green-Refactor 실행 방식은 [xp.md § TDD](docs/architecture/principles/xp.md).

**예외 없음**. 유저가 "일단 X 만들어봐" / "먼저 model 부터" 라 해도:
- "TDD 순서상 test 부터 작성하겠음. 승인?" **되물음**
- 승인 없이 프로덕션 파일 생성/편집 금지

**위반 판정**: 같은 slice 에 관련 test 없이 프로덕션 파일 만듦 (백엔드 기준 `tests/` 없이 `src/`).

**적용 범위**: 계층 무관 ([ADR 2026-08-14](docs/decisions/2026-08-14-cross-cutting-rule-placement.md)).

---

## 언제 무엇을 볼까

| 상황 | 문서 |
|------|------|
| 이 기능이 제품 방향에 맞나 / 우선순위 판단 | [product-vision.md](docs/product-vision.md) |
| 커밋 메시지 형식 (상세 규칙·예시) | [git-workflow.md § Commit 메시지](docs/git-workflow.md) |
| GitHub 액션(Issue/PR/마일스톤/라벨) 전 사용자 검토 | [github-strategy.md § GitHub 액션 전 사용자 검토 필수](docs/github-strategy.md) |
| 프론트엔드 설계 (Vue/Pinia, 도메인 매핑) | [frontend.md](docs/frontend.md) |
| 커밋 단위 (원자성, 언제 커밋할지) | [git-workflow.md § 원자적 커밋](docs/git-workflow.md) |
| 순수 docs 변경은 어떻게 (직접 master?) | [git-workflow.md § 문서 전용 변경](docs/git-workflow.md) |
| 브랜치 만들 때 / PR 만들 때 (단위·이름·master green 규칙) | [git-workflow.md § 브랜치 전략](docs/git-workflow.md) |
| PR 크기 (언제 분리?) | [git-workflow.md § PR 크기 원칙](docs/git-workflow.md) |
| Walking Skeleton PR 구성 (모든 계층 스텁) | [xp.md § Walking Skeleton 스텁 규칙](docs/architecture/principles/xp.md) |
| 개발 플로우 (Spike → Spec → Plan → Tasks → Skeleton → 구현) | [workflow.md](docs/workflow.md) |
| PR 생성 체크리스트 (milestone/label/template) | [github-strategy.md § PR 생성 체크리스트](docs/github-strategy.md) |
| PR 리뷰 (severity, nit 상한, 저자 응답 형식) | [review-standard.md](docs/review-standard.md) |
| Issue / Milestone / Label | [github-strategy.md](docs/github-strategy.md) |
| 새 slice 시작 (Spec/Plan/Task 순서) | [vertical-slices.md](docs/architecture/principles/vertical-slices.md) |
| TDD 순서 헷갈림 (Red-Green-Refactor, GWT) | [xp.md](docs/architecture/principles/xp.md) |
| 도메인 계층 애매 (4계층 어디에?) | [ddd.md](docs/architecture/principles/ddd.md) |
| 새 모듈 폴더 위치 & 모듈 "간" 경계 (`public.py`, 버스) | [modular-monolith.md](concenews-backend/docs/architecture/modular-monolith.md) |
| 모듈 "안" 4계층 구조 (어느 계층에 무엇을 넣나) | [module-internals.md](concenews-backend/docs/architecture/module-internals.md) |
| 계층 간 주고받는 타입 (dict 써도 되나, Domain 모델 API 노출) | [boundaries.md](concenews-backend/docs/architecture/boundaries.md) |
| DDD 4계층과 모듈 경계가 어떻게 맞물리나 | [integration.md](concenews-backend/docs/architecture/integration.md) |
| 백엔드 slice 세부 설계 | `concenews-backend/docs/plan-{slice}.md` |
| Docstring 형식 (Google style) | [docstring.md](concenews-backend/docs/conventions/docstring.md) |
| Domain immutability (frozen, tuple 등) | [immutability.md](concenews-backend/docs/conventions/immutability.md) |
| 테스트 구조 & 파일 위치 (unit/integration/acceptance) | [testing.md](concenews-backend/docs/conventions/testing.md) |
| Scheduler/Worker 구현·운영 규약 | [scheduled-workloads.md](concenews-backend/docs/conventions/scheduled-workloads.md) |
| ADR (아키텍처 결정 이력) | [docs/decisions/](docs/decisions/) — index: [README](docs/decisions/README.md) |
| ADR 프로세스 (언제/어떻게 쓰나) | [adr-process.md](docs/adr-process.md) |
| Spike 프로세스 | [spike-process.md](concenews-backend/docs/spike-process.md) |
| Spike/조사 결과 참조 | [docs/research/](docs/research/README.md) |

---

## UV 명령 실행

프로젝트 루트에서 백엔드 명령 실행:

```bash
uv --directory concenews-backend run pytest
uv --directory concenews-backend run python -m uvicorn src.main:app --reload
uv --directory concenews-backend run python script.py
```

백엔드 폴더로 이동한 경우는 `uv run {cmd}`. 설치·마이그레이션 등 초기 설정은 [README § 빠른 시작](README.md).
