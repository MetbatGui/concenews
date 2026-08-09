# GitHub Strategy

> Vertical Slice 기반 1인 개발의 GitHub 관리
> 기술적 명확성 & 체계적 히스토리

---

## 핵심 원칙

- **Epic**: Bounded Context 단위의 상위 Issue
- **Slice**: 사용자 가치가 있는 하위 Issue
- **Task**: `plan-{slice}.md`에 정의하고 PR 하나로 구현
- **Milestone**: 릴리스 버전
- **Branch**: `feature/{slice-name}-{task}`
- **Commit**: 명확한 메시지 (WHAT + WHY)
- **PR**: Self-review 기반

---

## ✨ GitHub 액션 전 사용자 검토 필수

**GitHub POST (이슈/PR/마일스톤/라벨 생성) 전에 반드시 사용자 검토 요청**:

```
Spec/Plan 작성 → [사용자 검토 대기] → GitHub 액션 (이슈/PR 생성)
```

- **Issue 생성** 전: "Issue 생성할 준비됨. 검토?"
- **PR 생성** 전: "PR 생성할 준비됨. 검토?"
- **Milestone 할당** 전: 사용자 지시 따름

사용자 명시적 승인 없이는 로컬 상태만 유지.

---

## 1. Milestones (Release)

### 구조
```
v0.1        (뉴스 조회·수집)
v0.2        (마켓 분류)
v0.3        (뉴스-마켓 매칭)
```

각 Milestone은 여러 Slice를 묶는 릴리스 범위다. 필요할 때만 due date와 태그를 사용한다.

---

## 2. Issues (Epic과 Slice)

### Issue 생성 시기

**Plan까지 완료 후** (개발 직전):

```
1. Spike (로컬, 학습)
2. Spec 작성 (사용자 관점)
3. Plan 작성 (설계 완료)
   ↓
4. Epic 또는 Slice Issue 생성 ← GitHub에 공식화
5. `feature/{slice}-{task}` 브랜치 시작
```

이유: 설계가 명확할 때 Issue 생성 → 개발 시작 → PR 연결

### Epic과 Slice 정의

```
Epic Title: [market] Market Bounded Context
Slice Title: [market-classification] 매크로 마켓 분류

Epic Labels: epic
Slice Labels: type:feat, status:planning
Milestone: 릴리스 버전 (필요한 경우)

## Spike
- [Spike 결과](../path/to/spec.md)

## What
- 사용자 관점: AC(Acceptance Criteria)

## Plan
- [설계](../path/to/plan.md)
```

### 예시: Slice
```
[news-fetch] 뉴스 조회

Parent: News Bounded Context Epic
Milestone: v0.1 (선택)
Labels: type:feat, status:planning

## Spike
- NewsAPI 선택 이유, 응답 형식 확인
- [스펙](../concenews-backend/docs/spec-news-fetch.md)

## What
- GET /news → 최근 뉴스 50개 반환
- 필드: id, title, link, description, source, published_at

## Plan
- [설계](../concenews-backend/docs/plan-news-fetch.md)
```

---

## 2.5 Bug Reports (언제 생성)

### Bug Report 작성 시점

**TDD 사이클 중**:
- RED 단계: Integration test 실패 → 미구현 (버그 아님)
- GREEN 단계: 개발 중 test 실패 → 디버깅 (버그 아님)
- REFACTOR 단계: 리팩터링 (버그 아님)

**버그 리포트 필요한 경우** (예상 밖의 문제):
- 기존 코드에서 발견한 결함
- Test 통과 후 수동 테스트에서 발견
- 외부 의존성 문제 (API 변경, 라이브러리 버그 등)

### 정리

```
TDD 자동 감지 → 버그 리포트 거의 불필요
예상 밖 이슈 발견 → Bug Report 생성 + 필요 시 다음 릴리스 Milestone 지정
```

### Bug Report 라벨
```
type:fix
priority: high/medium/low (필요시)
```

---

## 3. Branches & PRs

### 흐름
```
feature/news-fetch-{task} (Spike 완료 후)
  ├─ commit 1: Fix: NewsAPI parsing error
  ├─ commit 2: Feat: NewsRepository.find_all()
  ├─ commit 3: Refactor: extract _parse_response()
  │
  └─ Push → Create PR
              ├─ Title: [feature] News Fetch Slice
              ├─ Link Epic & Spike
              ├─ Self-review
              └─ Merge (regular) & delete branch
```

### PR 체크리스트
```markdown
## ✅ Ready
- [x] All tests green (Integration + Unit)
- [x] Self-reviewed (diff 명확한가?)
- [x] Refactored (중복 없나?)
- [x] Commit 메시지 명확한가?
```

### PR 생성 체크리스트

PR 만들 때 (`gh pr create` 전) 확인:

1. Base branch = master?
2. 릴리스 Milestone이 정해졌다면 Slice Issue에 할당됐는가?
3. Label 붙임? (`type:feat` / `type:fix` / `type:docs` / `type:refactor`)
4. Template body 준수? ([.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md))
5. 관련 이슈 링크? (마지막 slice PR 이면 `Closes #N`)

---

## 4. Commits (히스토리 명확성)

### 규칙

타입 + 간단한 설명 + 왜인지:

```
✨feat: NewsRepository 구현

NewsAPI에서 뉴스를 fetch하고 저장하는 로직.
Integration Test: test_get_news_returns_articles

🐛fix: NewsAPI 응답 KeyError 처리

비어있는 description 필드는 None으로 처리.

♻️refactor: NewsAPI 파싱 로직을 _parse_response() 메서드로 추출

중복 제거 + 단일 책임.
```

### 보이는 것

`git log master`:
```
abc123 Merge PR #1: [feature] News Fetch Slice
123abc Refactor: NewsAPI 파싱 로직 메서드 추출
456def Feat: NewsRepository 구현
789ghi Fix: NewsAPI KeyError 처리
```

→ "각 단계를 신중하게 구현했네" 느낌

---

## 5. 설정 (GitHub)

### Branch Protection (master, 선택)

```
현재는 로컬 `just check-branch-green`과 self-review를 사용하며 보호 규칙을 강제하지 않는다.

향후 보호 규칙을 켠다면 문서 전용 변경의 direct-to-master 예외를 먼저 폐지하고 다음만 적용한다.

Require pull request before merging: ON
  ├─ Require status checks: OFF (GitHub Actions 미사용)
  └─ Require code reviews: OFF (self-review로 충분)
```

### PR Template (.github/pull_request_template.md)

실제 파일 [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md) 참고.

구조:
```markdown
## 개요
이 PR의 목표를 한 문장으로.

## 주요 변경사항
- 변경 1
- 변경 2

## 테스트 계획
### 실행한 테스트
### 결과
- [ ] 모든 테스트 통과
- [ ] 새 테스트 추가됨
- [ ] 기존 테스트 영향 없음

## 검수 목록
- [ ] 코드 명확한가?
- [ ] 테스트 충분한가?
- [ ] 문서 업데이트되었나?
- [ ] import-linter 통과?

## 관련 이슈
Closes #00 (해당하면)

## 추가 노트
```

---

## 3. Labels

GitHub Issues 를 분류/추적.

**간단 규칙** (1인개발): Epic에는 `epic`, Slice와 PR에는 변경 유형(`type:*`)을 붙인다.

**예시**:
```
Issue #30: [news-collection] 뉴스 수집
Labels: type:feat, status:in-progress

Issue #35: [news-fetch] NewsAPI parser bug
Labels: type:fix
```

### 라벨 목록

**이슈 타입**:
```
epic            (Bounded Context 상위 Issue)
```

**변경 유형**:
```
type:feat       (새 기능)
type:fix        (버그 수정)
type:docs       (문서)
type:refactor   (리팩터링)
```

**Status** (선택, GitHub automation 가능):
```
status:in-progress  (진행 중)
status:done         (완료)
```

---

## 4. Release & Tags (선택)

릴리스 Milestone 완료 시 태그 생성:

```
v0.1, v0.2, v0.3...
```

필요시 나중에 (빠른 개발 우선).

---

## 5. PR과 Issue 연결

### 자동화 (GitHub)

PR 본문에 Issue 링크:

```
모든 PR:
  "Related to #{issue_number}" (또는 본문에 #N 언급)

Slice 마지막 PR:
  "Closes #{issue_number}" (merge 시 자동 close)

예:
PR #1: Related to #1
PR #2: Related to #1
PR #3: Closes #1 ← 마지막
  (PR #3 merge → Issue #1 자동 close)
```

---

## 요약

| 항목 | 규칙 |
|------|------|
| Epic | Bounded Context 상위 Issue |
| Slice | Epic의 하위 Issue |
| Task | Plan 체크리스트의 PR 하나 |
| Milestone | 릴리스 버전 |
| Labels | Epic은 `epic`, 변경은 `type:*`, 상태는 `status:*` |
| Branch | feature/{slice}-{task} |
| Commit | 명확한 메시지 (WHAT+WHY) |
| PR | Self-review 기반, regular merge |
| Release | v0.1, v0.2... (Milestone 완료 후) |
| Automation | "Closes #N" (마지막 PR이 Issue close) |
