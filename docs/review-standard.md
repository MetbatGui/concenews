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

## 고정 리뷰 템플릿

모든 독립 리뷰는 아래 구조를 **생략 없이** 사용한다. 해당 finding이 없으면 `없음`이라고 쓴다.

```markdown
# Caveman Review

**Overall**: 병합 가능 여부와 가장 중요한 위험을 한 문장으로 요약한다.

---

## 🔴 Bug

- `파일:행`: 실제 잘못되는 동작. 영향. 구체적 수정 방향.

## 🟡 Risk

- `파일:행`: 아직 실패하지 않았지만 취약한 계약. 영향. 구체적 수정 방향.

## ❓ Questions

- `파일:행`: 코드만으로 결정할 수 없는 의도·운영 정책 질문.

## 🔵 Nits

- `파일:행`: 선택적 개선. PR 크기별 nit 상한을 따른다.

---

## 필수 점검

- [ ] PR 범위와 Slice·Task·Issue 연결이 일치하는가?
- [ ] 테스트가 요구 계약을 실제로 증명하는가?
- [ ] 외부 HTTP·시간·네트워크 경계가 Fake 또는 격리됐는가?
- [ ] readiness·timeout·cleanup을 포함해 검증이 결정적인가?
- [ ] 컨테이너·배포 변경이면 환경 변수·secret·healthcheck·signal·restart를 검토했는가?

## Summary

| Severity | Count |
|---|---:|
| 🔴 bug | N |
| 🟡 risk | N |
| ❓ q | N |
| 🔵 nit | N |
```

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

처리 주체는 severity 가 결정한다 ([ADR 2026-08-14](decisions/2026-08-14-review-response-policy.md)).

### 형식 (권장)

```markdown
## 저자 응답

### 🟡 Risk & ❓ Questions

| Finding | Decision | Reason |
|---------|----------|--------|
| 🟡 X | accept | 실 데이터에 없음 |
| ❓ Y | defer | 다음 PR 결정 |

### 🔴 Bugs & 🔵 Nits

자동 수정 완료. 조치 내용은 `# Caveman Review 조치` 참고.
```

### 원칙

- 🔴/🔵 = 리뷰어가 **자동 수정**. 결정 여지가 없다 (bug 는 merge 블록이라 fix 외 선택지가 없고, nit 은 저자 재량)
- 🟡/❓ = 사용자 **명시적 결정 필수** (accept/defer/fix). 정의 자체가 결정을 요구한다
- 결정 전에는 해당 결정을 전제한 코드를 변경하지 않는다
- Defer = 후속 PR/이슈 명시
- 자동 수정분은 `# Caveman Review 조치` 댓글에 조치·검증 결과 기록

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
- 자동화 config 변경 (`just check-branch-green`으로 검증)
- 브랜치 정책 위반 없음 + tests green

**스킵 불가**:
- src/ 로직 변경
- Public API / DTO 변경
- 새 모듈/파일 추가
