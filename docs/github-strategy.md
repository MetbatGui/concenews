# GitHub Strategy

> Vertical Slice 기반 1인 개발의 GitHub 관리
> 기술적 명확성 & 체계적 히스토리

---

## 핵심 원칙

- **Milestone**: Slice 단위 (각 기능 = 1 Milestone)
- **Issue**: Epic (Slice 정의만, 세부 tasks는 docs/tasks.md)
- **Branch**: feature/{slice-name}, 모든 commit 보임 (regular merge)
- **Commit**: 명확한 메시지 (WHAT + WHY)
- **PR**: Self-review 기반

---

## 1. Milestones (Slice = Feature)

### 구조
```
news-fetch        (Slice #1)
market-info       (Slice #2)
matching          (Slice #3)
```

각 Milestone:
- Due date: 예상 완료일 (보통 1-2일)
- 완료 후: 관련 v0.1, v0.2... Release 태그 연결

---

## 2. Issues (Epic)

### Issue 생성 시기

**Plan까지 완료 후** (개발 직전):

```
1. Spike (로컬, 학습)
2. Spec 작성 (사용자 관점)
3. Plan 작성 (설계 완료)
   ↓
4. Issue 생성 ← GitHub에 공식화
5. Feature 브랜치 시작
```

이유: 설계가 명확할 때 Issue 생성 → 개발 시작 → PR 연결

### Epic 정의

```
Title: [epic-slug] 기능명

Labels: epic, {slug}
Milestone: {slice-name}

## Spike
- [Spike 결과](../path/to/spec.md)

## What
- 사용자 관점: AC(Acceptance Criteria)

## Plan
- [설계](../path/to/plan.md)
```

### 예시
```
[news-fetch] News API 통합

Milestone: news-fetch
Labels: epic, news-fetch

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
예상 밖 이슈 발견 → Bug Report 생성 + Milestone 없음 (urgent)
```

### Bug Report 라벨
```
type: bug
priority: high/medium/low (필요시)
```

---

## 3. Branches & PRs

### 흐름
```
feature/news-fetch (Spike 완료 후)
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

`git log main`:
```
abc123 Merge PR #1: [feature] News Fetch Slice
123abc Refactor: NewsAPI 파싱 로직 메서드 추출
456def Feat: NewsRepository 구현
789ghi Fix: NewsAPI KeyError 처리
```

→ "각 단계를 신중하게 구현했네" 느낌

---

## 5. 설정 (GitHub)

### Branch Protection (main)

```
Require pull request before merging: ON
  ├─ Dismiss stale PR approvals: ON
  ├─ Require status checks: OFF (1인이라 불필요)
  └─ Require code reviews: OFF (self-review로 충분)
```

### PR Template (.github/pull_request_template.md)

```markdown
## Spike
- [스펙](../docs/spec-{slug}.md)

## What Changed
- 기능 A
- 기능 B

## Checklist
- [ ] All tests green
- [ ] Self-reviewed
- [ ] Refactored
```

---

## 3. Labels

GitHub Issues를 분류 추적:

### Epic Labels
```
epic          (모든 Epic 이슈에 적용)
{slice-name}  (news-fetch, market-info 등)
```

### Type Labels (PR/Issue 변경 유형)
```
type:feat     (새 기능)
type:fix      (버그 수정)
type:docs     (문서)
type:refactor (리팩터링)
```

### Status Labels (진행상황, 선택)
```
status:planning     (계획 중)
status:in-progress  (진행 중)
status:done         (완료)
```

---

## 4. Release & Tags (선택)

Milestone 완료 시 태그 생성:

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
| Milestone | Slice 단위 (news-fetch, market-info...) |
| Issue | Epic (정의만, 링크 포함) |
| Labels | epic + type (feat/fix/docs) + status (선택) |
| Branch | feature/{slice} |
| Commit | 명확한 메시지 (WHAT+WHY) |
| PR | Self-review 기반, regular merge |
| Release | v0.1, v0.2... (Milestone 완료 후) |
| Automation | "Closes #N" (마지막 PR이 Issue close) |
