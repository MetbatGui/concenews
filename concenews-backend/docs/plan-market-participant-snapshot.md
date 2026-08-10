# Plan: 상위 보유 포지션 스냅샷 수집

**Spec**: [spec-market-participant-snapshot.md](./spec-market-participant-snapshot.md)  
**상태**: 검토 요청

## 설계 요약

마켓 스냅샷에 Gamma의 `condition_id`를 추가해, 이미 선택된 거래량 상위 매크로 마켓을 Data API 입력과 연결한다. 참여자 수집기는 가장 최근 스냅샷의 마켓별 식별자 쌍을 읽고, 각 `condition_id`로 결과별 상위 20개 보유 포지션을 수집한다.

```text
참여자 Scheduler (5분)
  -> MarketParticipantSnapshotService.run()
       -> PostgreSQL: 최신 마켓 스냅샷의 추적 대상 최대 50개
       -> Data API: /holders?market={conditionId}&limit=20
       -> PostgreSQL: market_participant_snapshot 저장
```

외부 HTTP 변환은 새 `ParticipantSourcePort`와 Data API adapter에 둔다. 추적 대상 조회·저장은 새 `ParticipantSnapshotRepositoryPort`에 둔다. 원시 보유량과 포지션 불변 조건은 Domain에 둔다.

## Task 1 — 식별자 계약·Domain·Repository Walking Skeleton

**브랜치/PR**: `codex/market-participant-snapshot-domain-repository`

- `MarketSnapshot`·payload·ORM에 nullable `condition_id` 추가 및 Alembic 마이그레이션
- `MarketParticipantSnapshot` 불변 Domain 모델과 저장소 Port·PostgreSQL adapter 추가
- 최신 마켓 스냅샷에서 `condition_id`가 있는 추적 대상 최대 50개를 조회하는 계약 추가
- 실제 PostgreSQL에서 마켓 식별자와 참여자 포지션이 보존되는 Integration Test 작성

**완료 기준**: 실제 DB에서 과거 스냅샷은 읽히고, 새 식별자 쌍과 참가자 포지션이 손실 없이 저장된다.

## Task 2 — Data API adapter와 수집 Service

**브랜치/PR**: `codex/market-participant-snapshot-service`

- Spike fixture를 `tests/fixtures/`의 단일 진실원천으로 정리
- Data API `/holders` 응답을 Domain payload로 변환하는 adapter 구현
- 최신 추적 대상마다 결과별 상위 20개 보유 포지션을 수집·저장하는 Service 구현
- 개별 마켓 외부 API 실패 격리와 빈 응답 처리 검증

**완료 기준**: 실제 PostgreSQL + MockTransport 조합에서 여러 결과 token의 포지션이 원시 보유량 그대로 저장되고, 한 마켓 실패가 다른 마켓 수집을 막지 않는다.

## Task 3 — Scheduler 조립과 영속성 경계

**브랜치/PR**: `codex/market-participant-snapshot-scheduler`

- Composition Root에 참여자 수집 작업 등록
- 기본 주기 `MARKET_PARTICIPANT_SNAPSHOT_INTERVAL=300` 추가
- 작업별 Session·HTTP client의 commit/rollback/close 경계 구현
- 새 Session으로 읽어 commit 경계를 검증하는 Integration Test 추가

**완료 기준**: Scheduler 작업이 실제 DB에 포지션을 commit하며, 실패가 다음 주기 실행을 막지 않고 `just check-branch-green`이 통과한다.

## 테스트 전략

Classicist 원칙에 따라 Domain·Service·Repository를 실제 조합하고, PostgreSQL을 Integration Test에 사용한다. 오직 시간·Scheduler·Data API HTTP 경계만 fake로 대체한다. 실제 외부 API 호출은 E2E 수동 검증으로 분리한다.

## Definition of Done

- [ ] Task 1~3 PR이 각각 merge commit으로 `master`에 병합됨
- [ ] `just check-branch-green` 통과
- [ ] 실제 PostgreSQL Integration Test가 신규 스키마·수집 Service·Scheduler commit 경계를 검증함
- [ ] 실제 Data API 검증은 `just check-e2e`에서 수동으로 실행하고 결과를 PR에 기록함
- [ ] 원시 관측값을 자금 규모나 참여자 정체성으로 과장하지 않음
