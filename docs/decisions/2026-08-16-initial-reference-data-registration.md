# ADR: 초기 참조 데이터를 프로세스 진입점에서 등록

**Status**: Accepted
**Date**: 2026-08-16
**Slice**: Cross-cutting

## Context

관측 제외 목록 Slice 는 Spike 근거를 가진 초기 지갑 1건을 DB 에 등록해야 한다 ([ADR 2026-08-15](./2026-08-15-market-participant-observation-eligibility.md)). 등록 경로에는 세 가지 요구가 있다.

- **멱등성**: 재기동·재배포마다 실행되어도 행이 늘지 않아야 한다.
- **Domain 계약 통과**: 지갑 주소 정규화와 "검토 완료 전 활성화 금지" 는 `MarketParticipantObservationExclusion` 의 validator 가 강제한다. 등록 경로가 이 계약을 우회하면 제약이 반쪽이 된다.
- **누락 시 침묵 금지**: 등록이 안 된 채로 시스템이 돌면 제외 목록이 빈 상태로 신호가 계산되고, 그 사실이 드러나지 않는다.

초기 구현은 `run_scheduler()` 안에서 등록을 호출했다. 그 결과 Scheduler 생명주기 함수가 DB 쓰기에 묶였고, 해당 unit test 전체가 `autouse` fixture 로 등록 호출을 대체해야 했다. PR #43 리뷰의 ❓-1 이 이 hidden dependency 를 지적했다.

이 결정은 market 모듈에 한정되지 않는다. 이후 어느 모듈이든 초기 참조 데이터가 생기면 같은 질문이 반복된다.

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| A. Alembic data migration | 배포 파이프라인의 `alembic upgrade` 에 묻어간다. 앱 코드가 관여하지 않는다. "reference data belongs in migrations" 라는 주류 권장에 부합 | raw SQL 이라 Domain validator 를 우회한다. 정책 데이터 변경이 스키마 이력에 섞여, 마이그레이션 로그가 스키마 진화와 정책 변경 두 가지를 동시에 담는다 |
| B. Scheduler 생명주기 (`run_scheduler`) 안 | 별도 배포 단계 없이 자동 실행 | seeding 이 정상 실행 흐름에 섞인다. 생명주기 함수가 DB 에 묶여 unit test 가 hidden dependency(autouse fixture)를 갖는다 |
| C. 프로세스 진입점 (`main`) | 실행 전 별도 초기화 단계로 분리된다. Domain 모델을 경유해 validator 를 통과한다. 생명주기 코드는 DB 와 무관해진다 | SIGTERM handler 설치 이전 구간에서 실행된다 |
| D. 수동 스크립트 | 앱 실행과 완전히 무관하다 | 배포 때마다 사람이 기억해야 한다. 잊으면 실패가 드러나지 않는다 |

## Decision

**옵션 C 채택.** 초기 참조 데이터 등록은 프로세스 진입점(`main`)에서 애플리케이션 실행 **이전에** 1회 수행한다.

- 등록 함수는 자체 Session 을 열고 commit 한 뒤 닫는다. 생명주기 코드는 등록을 알지 못한다.
- 등록할 값은 Domain 모델 인스턴스로 선언해 validator 를 통과시킨다.
- 멱등성은 DB 제약과 `on_conflict_do_nothing` 으로 보장한다. 애플리케이션의 존재 확인 후 삽입에 의존하지 않는다.
- 등록 실패는 삼키지 않고 전파해 프로세스 기동을 실패시킨다.

## Rationale

**Composition Root 는 엔트리 포인트에 위치한다.** Mark Seemann 의 정식화는 "A Composition Root should be located near the point where user code first executes" 이며, 엔트리 포인트를 "the user code that the framework calls first" 로 정의한다. 초기 데이터 등록은 조립·초기화 성격이지 실행 중 발생하는 생명주기 이벤트가 아니다. `main` 이 그 자리다.

**A 를 거부한 이유.** seeding 을 앱 실행에서 분리하라는 주류 권장의 근거는 세 가지인데, 우리 상황에는 모두 적용되지 않는다.

- 다중 인스턴스 race — Scheduler 는 단일 프로세스이며([ADR 2026-08-10](./2026-08-10-scheduler-runtime-daemon.md)), 등록은 `on_conflict_do_nothing` 이라 동시 실행에도 안전하다.
- DDL 권한 — 스키마를 바꾸지 않는다. INSERT 한 건이다.
- 롤링 업데이트 중 구/신 버전 충돌 — 스키마가 아니라 데이터이고 추가만 한다.

반면 A 의 비용은 실재한다. 마이그레이션은 raw SQL 로 삽입하므로 주소 정규화와 활성화 규칙을 강제하는 Domain validator 를 통과하지 않는다. 제외 목록은 신호의 의미를 바꾸는 정책 데이터이고, 그 무결성을 검증 없이 넣는 경로를 만들면 이후 항목 추가가 전부 그 경로를 따라간다.

같은 권장이 제시하는 대안이 "a dedicated initialization process" 이며, `main` 에서 실행 전 1회 수행하는 것이 그 형태다. 즉 C 는 주류 권장을 어긴 것이 아니라 그중 다른 쪽 갈래다.

**B 를 거부한 이유.** 생명주기 함수에 DB 쓰기를 넣으면 그 함수를 호출하는 모든 테스트가 등록을 대체해야 한다. 실제로 `autouse` fixture 가 생겼고, 그 fixture 는 이후 추가되는 테스트에도 보이지 않게 적용되어 공허하게 통과하는 검증을 만들 수 있다. 호출 위치를 옮기면 대체할 대상 자체가 사라지므로 fixture 를 삭제할 수 있다.

**대가.** 등록이 SIGTERM handler 설치보다 앞서므로, 그 구간에 종료 신호를 받으면 기본 동작으로 프로세스가 종료된다. 이 시점에는 정리할 Scheduler 가 없고 DB 트랜잭션은 연결 종료와 함께 서버가 롤백한다. 잃는 상태가 없다. "Scheduler start 중 SIGTERM 이 와도 stop 이 호출된다" 는 기존 계약은 그대로 유지된다.

**D 를 거부한 이유.** 실행 누락이 조용한 오동작으로 이어진다. 제외 목록이 비어 있어도 시스템은 정상처럼 보이고, 신호만 틀린다.

## Reconsider When

- Scheduler 가 다중 인스턴스로 확장될 때. 멱등성은 유지되지만 기동마다 중복 시도가 발생하므로 등록 위치를 재검토한다.
- 초기 데이터가 사람이 편집하는 규모로 커질 때. 코드 상수는 더 이상 적절하지 않다.
- 등록 실패로 인한 기동 실패가 운영상 문제가 될 때. 그 경우 실패를 경고로 낮출지 결정한다.

## References

- [Composition Root location — Mark Seemann](https://blog.ploeh.dk/2019/06/17/composition-root-location/)
- [Data Seeding — EF Core, Microsoft Learn](https://learn.microsoft.com/en-us/ef/core/modeling/data-seeding)
- [ADR 2026-08-15 마켓 참여자 관측 자격](./2026-08-15-market-participant-observation-eligibility.md)
- [ADR 2026-08-10 Scheduler 실행 데몬](./2026-08-10-scheduler-runtime-daemon.md)
- [plan-market-participant-observation-eligibility.md](../../concenews-backend/docs/plan-market-participant-observation-eligibility.md) — Task 1
