# Plan: 마켓 참여자 관측 자격

**Spec**: [spec-market-participant-observation-eligibility.md](./spec-market-participant-observation-eligibility.md)
**상태**: 검토 요청

## 설계 요약

원본 `MarketParticipantSnapshot`은 수집 시점에 그대로 저장한다. 별도 `MarketParticipantObservationExclusion` aggregate가 사람이 검토한 제외 목록을 보존하고, 상위 참여자 관측을 읽는 application service가 활성·검토 완료 항목만 결과에서 제거한다.

```text
Data API -> 원본 MarketParticipantSnapshot 저장
                         |
                         | 원본은 변경하지 않음
                         v
관측 조회 Service <- 활성·검토 완료 제외 목록
       -> 관측 가능 상위 참여자 목록
       -> 이후 포지션 변화 신호의 입력
```

제외 후보의 자동 탐지와 UI·HTTP API는 이 Slice 범위 밖이다. 초기 제외 항목은 마이그레이션 또는 명시적 bootstrap 데이터로 한 번만 등록하며, 실행마다 중복 생성하지 않는다.

## Task 1 — 제외 목록 Domain·저장소 Walking Skeleton

**브랜치/PR**: `feature/market-participant-observation-eligibility-exclusion`

- 실패하는 Unit Test부터 `MarketParticipantObservationExclusion` 불변 Domain 모델의 지갑 정규화·검토 상태·활성 중복 규칙 정의
- 제외 목록 Port와 PostgreSQL adapter, ORM, Alembic 마이그레이션 추가
- Spike 근거 URL을 가진 초기 지갑을 멱등적으로 등록하는 bootstrap 경로 추가. 등록은 프로세스 진입점에서 실행 전 1회 수행한다 ([ADR 2026-08-16](../../docs/decisions/2026-08-16-initial-reference-data-registration.md))
- 실제 PostgreSQL에서 초기 항목·근거·상태가 저장되고 재실행해도 중복되지 않는 Integration Test 작성

**완료 기준**: 초기 제외 지갑과 감사 메타데이터가 실제 DB에 한 번만 저장되고, 유효하지 않은 주소·중복 활성 항목은 저장되지 않는다.

## Task 2 — 관측 자격 조회와 원본 보존

**브랜치/PR**: `feature/market-participant-observation-eligibility-query`

- 원본 참여자 스냅샷 조회 Port와 관측 자격 application service 추가
- 활성·검토 완료 제외 목록만 적용하는 필터 구현
- 후보·비활성 항목은 통과시키고, 원본 보유량·마켓·결과·관측 시각을 바꾸지 않는 계약 구현
- 실제 PostgreSQL에서 원본 행은 남아 있고 관측 자격 조회 결과만 달라지는 Integration Test 작성

**완료 기준**: 제외 목록이 없는 경우 기존 결과와 같고, 초기 제외 지갑이 있을 때만 해당 지갑이 신호용 결과에서 빠진다.

## 테스트 전략

Classicist 원칙에 따라 Domain, application service, PostgreSQL repository를 실제로 조합한다. 외부 HTTP 호출은 추가하지 않는다. 초기 데이터 등록은 고정 sleep 없이 명시적 멱등성으로 검증한다.

## Definition of Done

- [ ] Task 1~2 PR이 각각 merge commit으로 `master`에 병합됨
- [ ] `just check-branch-green` 통과
- [ ] 원본 참여자 스냅샷이 제외 정책으로 수정·삭제되지 않음을 Integration Test가 증명함
- [ ] 활성·검토 완료 제외 항목만 신호용 관측에서 빠짐을 Integration Test가 증명함
- [ ] 후속 포지션 변화 신호 Slice가 이 관측 자격 조회를 입력으로 사용함
