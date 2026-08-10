# 개발 플로우 (Spec-Kit + Working Skeleton)

> Spec-Kit 툴 + Working Skeleton 패턴 + Integration Test 조합.
> **Milestone 완료 기준 = 모든 Integration Test pass**.

---

## 플로우 개요

```
간단 기획 → (Spike) → (ADR) → Spec → Plan → 사용자 검토 → Issue 생성 → Tasks → Walking Skeleton → 구현 → 부가 기능
                                                                                  ↑
                                                                  각 구현 단계 = Integration Test 로 검증
```

---

## 단계별 상세

### 1. 간단 기획 (5분)

- 기능 개요
- 입력/출력 정의

### 2. Spike (필요시, 30분~)

- 미확정 기술 조사 (외부 API 사용법, 데이터 구조 등)
- 임시 코드 실행 → `concenews-backend/spikes/{topic}/` (로컬, 삭제)
- Findings 문서화 → `docs/research/{topic}.md` (커밋)
- Spec 에 반영할 내용 준비
- 상세: [spike-process.md](../concenews-backend/docs/spike-process.md)
- 결과 기록 규약: [Spike 학습 결과 ADR](decisions/2026-08-10-spike-knowledge-recording.md)

### 3. ADR → `docs/decisions/YYYY-MM-DD-{slug}.md` (설계 결정 시)

- 모듈 경계, 저장소, 외부 의존성, 아키텍처 원칙, 프로세스 규칙은 ADR trigger 다.
- Spike가 있으면 학습 결과를 ADR의 Context와 Options에 반영한다.
- ADR은 결정 로그이고, 이후 Spec·Plan은 채택안을 최신 상태로 표현한다.
- 상세: [adr-process.md](adr-process.md)

### 4. Specify → `spec-{slice}.md`

- 입력/출력 명확히
- Acceptance Criteria (AC) 정의 (정입력/오류 케이스)

### 5. Plan → `plan-{slice}.md`

- Phase 1: Walking Skeleton (Stub + Integration 테스트, 모든 계층)
- Phase 2: 실제 구현 (Inside-Out TDD, Stub 하나씩 교체)
- Phase 3: 부가 기능 (Scheduler, Bootstrap DI 등)
- PR 스코프 평가 ([git-workflow.md § PR 크기 원칙](git-workflow.md))

### 6. 사용자 검토

- Spec과 Plan을 사용자에게 제시하고 승인받는다.
- 승인 전에는 구현 브랜치·프로덕션 코드·GitHub Issue/PR을 만들지 않는다.

### 7. GitHub Issue 생성 (GitHub로 추적하는 Slice만)

- 사용자가 명시적으로 승인한 경우에만 Epic 또는 Slice Issue를 생성한다.
- Issue는 승인된 Spec·Plan과 Research·ADR을 링크해 Slice의 공식 기록이 된다.
- Issue 생성 후 각 Task의 `feature/{slice}-{task}` 브랜치를 만든다.
- 작은 로컬 작업처럼 GitHub Issue로 추적하지 않는 경우에는 이 단계를 건너뛴다.
- 상세: [github-strategy.md](github-strategy.md)

### 8. Tasks

- [ ] Walking Skeleton (모든 계층 스텁, Integration test RED → GREEN)
- [ ] 실제 구현 (Repository, API client, ...)
- [ ] 부가 기능 (Scheduler, Bootstrap, Lifespan)

### 9. Implement

- Task 순서대로. **Task 하나 = PR 하나 = `feature/{slice}-{task}` 브랜치 하나**.
- 각 논리 단위 = 1 커밋 ([git-workflow.md § 원자적 커밋](git-workflow.md))
- Integration 테스트: 스텁 통과 → 실 구현 통과 (회귀 방지)

### 10. Self-review와 독립 리뷰

- PR 생성 전 `git-workflow.md`의 Self-review 최소 계약으로 범위·계약 증명·외부 경계·결정성·운영 계약을 확인한다.
- Draft PR 생성 뒤 별도 컨텍스트의 읽기 전용 Caveman Review를 수행하고 결과를 PR 댓글로 남긴다.
- 리뷰 finding은 사용자 수정 승인 뒤에만 변경하고, 조치 결과와 최신 검증 결과를 PR에 기록한 다음 병합한다.

### 11. Milestone 완료

- 모든 Integration Test pass
- Integration Test = Milestone 완료 기준

---

## 테스트 전략

**Walking Skeleton 단계:**

- 외부 HTTP 경계는 `tests/fixtures/`의 Spike 기반 fixture로 대체하고, 내부 구현체는 가능한 실제로 조합
- Integration Test: 입력 → 처리 → 응답/저장 확인
- 모든 계층 스텁 필수 ([xp.md § Walking Skeleton 스텁 규칙](architecture/principles/xp.md))

**구현 단계:**

- 실제 PostgreSQL 저장, 외부 HTTP 경계는 결정적 Fixture/Transport 유지
- 동일한 Integration Test (회귀 방지)
- 실제 외부 API는 E2E에서만 수동 검증

---

## 용어 정리

- **Integration Test ≠ E2E Test**
  - Integration: 실제 DB와 백엔드 컴포넌트를 조합하되 외부 HTTP 경계는 Fake로 대체
  - E2E: 실제 외부 서비스와 실제 DB를 함께 통과하는 전체 백엔드 흐름
- 본 플로우는 Integration Test 기반이며, E2E는 배포 전 수동 실행한다.
- UI 연결 후에는 UI까지 포함한 별도 E2E Test를 추가한다.

---

## GitHub 연동

- Epic Issue = Bounded Context 단위 (예: "Market Bounded Context")
- Milestone = 릴리스 버전 (v1.0, v1.1, ...)
- Slice = 하위 Issue (Epic 의 sub-issue)
- Slice Issue → Plan의 Task별 PR로 분해
- 상세: [github-strategy.md](github-strategy.md)
