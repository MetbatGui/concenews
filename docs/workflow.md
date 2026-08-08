# 개발 플로우 (Spec-Kit + Working Skeleton)

> Spec-Kit 툴 + Working Skeleton 패턴 + Integration Test 조합.
> **Milestone 완료 기준 = 모든 Integration Test pass**.

---

## 플로우 개요

```
간단 기획 → (Spike) → Spec → Plan → Tasks → Walking Skeleton → 구현 → 부가 기능
                                                    ↑
                                    각 단계 = Integration Test 로 검증
```

---

## 단계별 상세

### 1. 간단 기획 (5분)

- 기능 개요
- 입력/출력 정의

### 2. Spike (필요시, 30분~)

- 미확정 기술 조사 (외부 API 사용법, 데이터 구조 등)
- Findings 문서화 → `concenews-backend/spikes/{topic}/LEARNINGS.md`
- Spec 에 반영할 내용 준비
- 상세: [spike-process.md](../concenews-backend/docs/spike-process.md)

### 3. Specify → `spec-{slice}.md`

- 입력/출력 명확히
- Acceptance Criteria (AC) 정의 (정입력/오류 케이스)

### 4. Plan → `plan-{slice}.md`

- Phase 1: Walking Skeleton (Stub + Integration 테스트, 모든 계층)
- Phase 2: 실제 구현 (Inside-Out TDD, Stub 하나씩 교체)
- Phase 3: 부가 기능 (Scheduler, Bootstrap DI 등)
- PR 스코프 평가 ([git-workflow.md § PR 크기 원칙](git-workflow.md))

### 5. Tasks

- [ ] Walking Skeleton (모든 계층 스텁, Integration test RED → GREEN)
- [ ] 실제 구현 (Repository, API client, ...)
- [ ] 부가 기능 (Scheduler, Bootstrap, Lifespan)

### 6. Implement

- Task 순서대로
- 각 Task = 1 PR (원칙적으로), 각 논리 단위 = 1 커밋 ([git-workflow.md § 원자적 커밋](git-workflow.md))
- Integration 테스트: 스텁 통과 → 실 구현 통과 (회귀 방지)

### 7. Milestone 완료

- 모든 Integration Test pass
- Integration Test = Milestone 완료 기준

---

## 테스트 전략

**Walking Skeleton 단계:**

- Mock 외부 API (하드코딩 응답), In-memory Repository
- Integration Test: 입력 → 처리 → 응답/저장 확인
- 모든 계층 스텁 필수 ([xp.md § Walking Skeleton 스텁 규칙](architecture/principles/xp.md))

**구현 단계:**

- 실 API 호출, 실 DB 저장
- 동일한 Integration Test (회귀 방지)
- 실 동작 검증

---

## 용어 정리

- **Integration Test ≠ E2E Test**
  - Integration: 백엔드 컴포넌트 간 (API → DB)
  - E2E: 전체 사용자 흐름 (UI → DB → 화면)
- 본 플로우는 Integration Test 기반
- UI 연결 시 별도 E2E Test 추가

---

## GitHub 연동

- Epic Issue = Bounded Context 단위 (예: "Market Bounded Context")
- Milestone = 릴리스 버전 (v1.0, v1.1, ...)
- Slice = 하위 Issue (Epic 의 sub-issue)
- Tasks → 각 PR 로 변환
- 상세: [github-strategy.md](github-strategy.md)
