# PR Review 표준

> Caveman-style 리뷰. 얇은 PR / CI 정합 지향.

---

## 형식

### 구조
```markdown
# Caveman Review

**Overall**: (1줄 요약, blocker 유무)

---

## 🔴 Bug (있으면)
## 🟡 Risk (있으면)
## ❓ Questions (있으면)
## 🔵 Nits (있으면)

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 bug | N |
| 🟡 risk | N |
| ❓ q | N |
| 🔵 nit | N |
```

### Severity 정의

| 태그 | 뜻 | 예 |
|------|----|-----|
| 🔴 bug | 실제 깨진 동작, merge 블록 | null deref, 잘못된 조건 |
| 🟡 risk | 동작하지만 취약, 결정 필요 | race, retry 없음, error swallow |
| ❓ q | 판단 요청, 제안 아님 | "이 선택 이유?" |
| 🔵 nit | 취향/미세 개선, 저자 재량 | naming, 순서, docstring |

### Finding 표기

- **파일별 그룹핑**: `file:L{line}: <severity>: <problem>. <fix>.`
- **한 줄 원칙**: 여러 줄 필요하면 별도 subsection (severity 재고)
- **Location + Fix**: `L42: id positivity 없음. Field(gt=0) 추가` — 저자가 즉시 실행 가능

---

## Self-Limits (얇은 PR 정신)

리뷰어는 발굴 강박 지양. **PR 크기에 비례**하는 리뷰량:

| PR 크기 | 🔵 nit 상한 | 🔴/🟡/❓ |
|---------|-------------|-----------|
| < 100 라인 | ≤ 1 | 제한 없음 |
| 100~300 | ≤ 3 | 제한 없음 |
| 300~1000 | ≤ 5 | 제한 없음 |
| > 1000 | PR 분할 요청 | — |

**Nit 만 있는 리뷰**: 코멘트 스킵 가능. Merge 승인 button 만으로 대체.

---

## 저자 응답

리뷰 대응 시 각 finding 에 accept/defer/fix 결정 명시.

### 형식 (권장)

```markdown
## 저자 응답

### 🟡 Risk & ❓ Questions

| Finding | Decision | Reason |
|---------|----------|--------|
| 🟡 X | accept | 실 데이터에 없음 |
| ❓ Y | defer | 다음 PR 결정 |

### 🔵 Nits

모두 accept. 개별 refactor 스코프 확장 회피.
```

### 원칙

- 🔴/🟡/❓ = 명시적 결정 필수 (accept/defer/fix)
- 🔵 = 요약 accept 로 충분
- Defer = 후속 PR/이슈 명시

---

## 근거

- Google Code Review Guide: nit 은 저자 재량
- MSR (Microsoft) 연구: 리뷰 시간 vs 발견 이슈 = **30분 후 diminishing return**
- Continuous Integration: 리뷰 = merge 지연 요소. 최소화.
- 얇은 PR (< 300 라인): 리뷰 시간 15분 목표

---

## 언제 리뷰 스킵?

**스킵 가능**:
- 순수 docs 변경 (오타, 문구 갱신)
- 자동화 config 변경 (검증은 CI 가)
- 브랜치 정책 위반 없음 + tests green

**스킵 불가**:
- src/ 로직 변경
- Public API / DTO 변경
- 새 모듈/파일 추가
