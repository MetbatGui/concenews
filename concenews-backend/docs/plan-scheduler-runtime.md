# Plan: Scheduler Runtime 분리

**상태**: Accepted
**Spec**: [spec-market-classifier-scheduler.md](spec-market-classifier-scheduler.md)
**관련 결정**: [Scheduler Runtime ADR](../../docs/decisions/2026-08-10-scheduler-runtime-daemon.md)
**운영 규약**: [주기 작업 운영 계약](conventions/scheduled-workloads.md)

---

## 목표

뉴스 수집과 마켓 분류의 주기 실행을 API 프로세스에서 분리해 단일 Scheduler 컨테이너에서 실행한다. API는 HTTP 요청 처리만 담당한다.

## 작업 분해와 PR 경계

### Task 1. 공용 Scheduler와 작업 조립

**브랜치**: `feature/scheduler-runtime-daemon`
**상태**: 완료 (PR #31)

- `AsyncioSchedulerAdapter`를 `shared_kernel/scheduler/`로 이관한다.
- 뉴스·마켓 bootstrap에 “작업 하나를 Scheduler에 등록하는” 공개 조립 함수를 둔다.
- 작업별 환경 변수, 매 실행 Session 생성·종료, 작업명 포함 오류 로그를 구현한다.
- API와 Scheduler가 사용할 공용 조립 함수의 책임을 테스트로 고정한다.

**TDD 순서**:

1. 두 작업 등록·수동 실행·실패 격리를 확인하는 실패하는 Unit/Integration 테스트 작성
2. 공용 Adapter 이관과 작업 등록 함수의 최소 구현
3. 실제 PostgreSQL과 Fake 외부 경계로 두 저장 흐름 검증

### Task 2. Scheduler 진입점과 API 분리

**브랜치**: `feature/scheduler-runtime-entrypoint`
**상태**: 완료 (PR #32)

- `src/scheduler_main.py`에서 두 작업 등록, 시작, SIGTERM/KeyboardInterrupt 종료를 구현한다.
- `src/main.py`에서 Scheduler lifespan 시작 코드를 제거한다.
- API는 Scheduler 없이 기동되고, Scheduler는 API 없이 기동됨을 검증한다.

**TDD 순서**:

1. API가 Scheduler를 등록하지 않는 실패하는 테스트 작성
2. 진입점 lifecycle의 시작·정지 테스트 작성
3. 최소 구현 후 테스트 통과

### Task 3. 컨테이너 실행 구성

**브랜치**: `feature/scheduler-runtime-container`
**상태**: 완료

- 백엔드 이미지 Dockerfile을 추가한다.
- Compose에 동일 이미지를 서로 다른 명령으로 실행하는 `api`, `scheduler` 서비스를 추가한다.
- `postgres` healthcheck 이후 두 서비스가 시작되도록 설정한다.
- 환경 변수 전달과 로컬 실행 방법을 README에 문서화한다.
- 실제 외부 API를 호출하지 않는 컨테이너 기동·종료 검증을 추가한다.

## Walking Skeleton

이번 Slice는 기존 뉴스·마켓 서비스가 이미 실제 구현되어 있으므로 도메인 계층의 새 Stub이 필요 없다. 대신 **실행 경계**가 Skeleton이다.

```text
Scheduler 진입점
  → 공용 Scheduler Adapter
    → 뉴스 작업 조립 → Fake 외부 경계 → 실제 PostgreSQL
    → 마켓 작업 조립 → Fake 외부 경계 → 실제 PostgreSQL
```

Task 1에서 이 흐름을 수동 trigger 기반 Integration 테스트로 GREEN으로 만든 뒤, Task 2와 Task 3에서 프로세스·컨테이너 경계를 실제 구현으로 교체한다.

## 검증 전략

- Unit: interval 값, 작업 등록, 예외 격리, 종료 동작
- Integration: Fake 외부 HTTP 경계 + 실제 PostgreSQL의 뉴스·마켓 저장 흐름
- 컨테이너: 실제 외부 API 호출 없이 Scheduler 프로세스의 기동·종료와 API 비기동 독립성 확인
- E2E: 배포 전 `just check-e2e`로 실제 TheNewsAPI와 PostgreSQL 검증. Polymarket 실제 호출은 별도 수동 실행으로 유지
- 각 Task 완료 전 `just check-branch-green`

## 완료 조건

- [x] API 컨테이너가 Scheduler 없이 HTTP만 제공한다.
- [x] Scheduler 컨테이너가 뉴스 수집과 마켓 분류를 각각 등록한다.
- [x] 두 작업이 독립 Session을 사용하고 오류가 격리된다.
- [x] SIGTERM에 등록 작업이 정리된다.
- [x] API·Scheduler·PostgreSQL Compose 구성이 문서화되고 기동된다.
- [x] `just check-branch-green`이 통과한다.

## 승인 후 문서 정리

- 기존 [Scheduler 선택 ADR](../../docs/decisions/2026-07-06-scheduler-choice.md)을 Superseded 처리한다.
- [spec-market-tracking.md](spec-market-tracking.md)와 [plan-market-tracking.md](plan-market-tracking.md)의 FastAPI lifespan 서술을 새 런타임 결정으로 갱신한다.
