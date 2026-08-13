# Git Workflow

> 1인 개발자 기준, Vertical Slice + XP 프로세스 연계

---

## 브랜치 전략

### master
- 항상 배포 가능 (모든 테스트 green)
- PR 기반 merge (self-review 포함)

### feature/{slice-name}-{task}
```
feature/news-fetch-acceptance    (walking skeleton: acceptance test + stub, GREEN)
feature/news-fetch-domain        (Domain + unit test, GREEN)
feature/news-fetch-repository    (Repository + unit test + fixture, GREEN)
feature/news-fetch-service       (Service + unit test, GREEN)
feature/news-fetch-wire          (Endpoint wire-up + integration test, GREEN)
```
- **PR 단위 = TDD cycle 완결** (RED + GREEN + Refactor 결합).
- **브랜치 단위 = PR 단위 = Task 단위**: Task마다 master에서 새 `feature/{slice}-{task}` 브랜치를 만들고, 하나의 브랜치에는 하나의 PR만 둔다.
  TDD step (RED 만, GREEN 만) 을 별도 PR 로 나누지 않음.
- **매 PR merge 시 master green 보장** — RED 상태 master merge 금지.
- master 에서 생성, PR merge 후 삭제

---

## Spike (임시 코드는 로컬, 결과는 Git)

```
spikes/{topic}/
├── {api}_spike.py
```

**중요**: Spike는 브랜치 불필요
- 임시 코드만 로컬 폴더에서 실행하고 삭제
- 학습 결과는 `docs/research/{topic}.md`에 커밋
- 설계 결정은 ADR, 구현 범위는 Spec/Plan에 링크

---

## Commit 메시지

### 형식

```
{GITMOJI}{type}: {title}

{description}

- {detail}
- {detail}
```

### 규칙

- gitmoji는 type에 붙여서 작성 (`✨feat`, `🐛fix`)
- description 필수
- `-` 항목은 선택 (복잡한 작업만, 단순 작업은 title + description으로 충분)

### Gitmoji 매핑

| type     | gitmoji | 설명                           |
| -------- | ------- | ------------------------------ |
| feat     | ✨      | 새로운 기능 추가               |
| fix      | 🐛      | 버그 수정                      |
| refactor | ♻️    | 코드 리팩토링 (기능 변경 없음) |
| docs     | 📝      | 문서 추가/수정                 |
| test     | 🧪      | 테스트 추가/수정 (설계 포함)   |
| chore    | 🔧      | 빌드, 의존성, 설정 변경        |

### 예시

**복잡한 작업:**

```
✨feat: 뉴스 카드 컴포넌트 추가

뉴스 목록 페이지에서 각 기사를 표시하는 카드 UI 구현

- 썸네일, 제목, 요약, 날짜 필드 포함
- 클릭 시 상세 페이지로 라우팅
- 모바일 반응형 레이아웃 적용
```

**단순 작업:**

```
🔧chore: 환경 변수 설정 추가

.env.example 파일 추가 및 README에 설정 가이드 작성
```

### 원칙: 원자적 커밋 (Atomic Commits)

한 커밋 = 한 가지 변경사항. 여러 변경을 한 커밋에 묶지 않음.

**TDD 예시**:
```bash
# Commit 1: RED 상태 (test만)
🧪test: NewsItem validation unit tests

# Commit 2: GREEN 상태 (impl)
✨feat: NewsItem Pydantic model

# Commit 3: REFACTOR (필요시)
♻️refactor: NewsItem docstring 개선
```

**이점**:
- git log 이력 명확 (각 단계 추적 가능)
- Bisect 용이 (버그 원인 특정 쉬움)
- Revert 정밀함 (특정 변경만 되돌리기)

---

## 문서 전용 변경 (Direct-to-master 예외)

**순수 문서 변경 (코드 변경 없음) 은 브랜치/PR 없이 master 직접 commit & push**:

- 오타 수정, 정책 문서 갱신, ADR 추가, 체크리스트 추가 등
- **Why**: 1인 개발 + 문서 변경은 코드 리스크 없음. PR 왕복 = 오버헤드. 얇은 PR 정신 반대 방향.

**적용 규칙:**

- 코드 변경 없는 순수 docs → master 직접
- 코드 + 문서 섞이면 → PR
- 원칙 문서 (xp.md, ddd.md) 갱신 → 논쟁 여지 있으면 PR, 오타/보완이면 직접
- **작업 중 feature 브랜치에서 문서 변경 발생 시 → 그 브랜치에 그대로 커밋** (stash/switch to master 하지 말 것). Feature 흐름 유지 우선. Master 직접 커밋은 세션 시작 시 순수 문서 작업일 때만.
- Branch protection 걸려 있으면 임시 해제 or 사용자가 직접 push

---

## PR 크기 원칙

**작업이 크면 PR 분리. 각 PR = focused & compact.**

**Why**: 작고 focused PR → review 쉬움, merge 빠름.

**적용:**

- 사전 설계 단계 (Plan) 에서 PR 스코프 평가
- Multiple concerns ("bootstrap + lifespan" 등) → 분리. 분리된 각 concern은 별도 Task·PR·feature 브랜치다.
- 각 PR = 한 가지 책임 (scheduler impl / bootstrap DI / lifespan 각각)
- **Acceptance criteria: PR body 읽을 때 "그리고" 많으면 분리 신호**

**예시** (news-collection):

- PR #7a: Scheduler adapter + Integration test
- PR #7b: Bootstrap DI + lifespan

---

## Self-review 최소 계약

PR 생성 전 저자는 `origin/master...HEAD`를 읽고 다음 다섯 항목을 확인한다. 이 단계는 독립 리뷰를 대체하지 않으며, 얕은 범위 확인을 넘는 최소 안전장치다.

- **범위**: 변경 파일·커밋이 현재 Task와 PR 본문에만 대응하는가.
- **계약 증명**: 테스트가 요구한 동작이 깨지면 실제로 실패하는가. 단순 종료 코드나 로그 존재만 성공 조건으로 삼지 않는다.
- **외부 경계**: 테스트가 실제 외부 서비스에 요청을 시도하지 않고 Fake·fixture·격리된 transport를 사용하는가.
- **결정성**: 고정 sleep 대신 readiness·명시적 상태·제한 시간을 사용하고, cleanup 실패도 보고하는가.
- **운영 계약**: 환경 변수·secret 제외, healthcheck, signal, restart, volume·포트 충돌을 확인했는가.

Self-review에서 발견한 사항은 **PR 생성 전에 먼저 수정**하고 `just check-branch-green`을 다시 실행한다. 수정 뒤의 diff와 검증 결과를 확인한 커밋만 push·PR 생성 대상으로 삼는다. PR 본문에는 최종 self-review 결과와 선행 개선 사항을 요약한다.

---

## 독립 리뷰와 수정 승인

Ready PR을 연 뒤 Codex는 별도 컨텍스트의 읽기 전용 리뷰를 자동으로 수행하고, `# Caveman Review` 댓글로 결과를 남긴다. Draft PR은 구현 진행 상황 공유에만 사용하며 독립 리뷰를 시작하지 않는다.

1. 저자는 self-review에서 발견한 사항을 수정하고 전체 검증을 다시 통과한 뒤 Ready PR을 연다.
2. 독립 리뷰는 `Caveman Review` 형식으로 결함·위험·질문만 판정한다.
3. **Question이 없으면** Codex는 Bug·Risk·Nit finding을 자동 수정한다. Question이 있으면 사용자 결정 전에는 해당 결정을 전제한 코드를 변경하지 않는다.
4. 수정 뒤 `just check-branch-green`·커밋·push를 수행하고, `# Caveman Review 조치` 댓글로 변경·검증 결과를 남긴다.
5. 조치가 모두 검증되면 merge commit으로 병합한다.

### 병합 방식

Task PR은 **merge commit** 방식으로 병합한다. Task 안의 원자 커밋과 TDD·리뷰 이력을 보존해, `master`에서 변경의 흐름을 추적할 수 있게 한다.

- `gh pr merge --merge`를 사용한다.
- squash merge와 rebase merge는 사용하지 않는다.

---

## Pull Request

1인이지만 self-review 필수:
```bash
git diff master..feature/news-fetch
# → diff 읽고 refactor 필요 확인
# → 복잡도 없나, 명확한가?
```

PR 체크리스트:
- [ ] 모든 테스트 green
- [ ] diff 명확한가?
- [ ] 불필요한 코드 없나?
- [ ] Integration Test 통과했나?

---

## 병렬 Slice 없음

1인 개발 → 1번에 1 Slice만
- feature/x 진행 중 → feature/y는 안 함
- 완료 후 merge → 다음 Slice로

---

## 요약

| 단계 | 브랜치 | 액션 |
|------|--------|------|
| Spike (학습) | — (로컬) | 임시 코드 삭제 → `docs/research/{topic}.md` commit |
| ADR (설계 결정) | master | 결정 기록 후 Spec/Plan에 링크 |
| Spec 확정 | master | spec.md commit |
| 개발 | feature/{slice}-{task} | code → test → refactor |
| PR & Review | feature/{slice}-{task} | self-review → merge |
| 배포 | master | 자동화 또는 수동 |

