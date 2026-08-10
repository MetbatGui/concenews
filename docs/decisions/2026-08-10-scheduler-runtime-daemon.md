# ADR: Scheduler Runtime — 별도 컨테이너와 공용 실행기

**Status**: Accepted
**Date**: 2026-08-10
**Slice**: scheduler-runtime

---

## Context

기존 결정([scheduler-choice](./2026-07-06-scheduler-choice.md))은 뉴스 수집 작업 하나만 있었으므로 stdlib asyncio Scheduler를 news 모듈 내부에 두고 FastAPI lifespan에서 실행했다.

이제 뉴스 수집과 마켓 분류라는 두 주기 작업이 있다. API 프로세스의 재시작·수평 확장은 Scheduler의 재시작·중복 실행을 유발할 수 있고, 한 프로세스의 장애 경계도 불명확하다. 기존 ADR의 재검토 조건인 두 번째 모듈의 Scheduler 사용 및 별도 daemon 필요 조건에 해당한다.

Spike [Research 기록](../research/scheduler-runtime.md)에서 기존 Adapter의 다중 작업 등록·시작·정지와 두 모듈의 독립 조립 가능성을 확인했다.

## Options Considered

| 옵션 | 장점 | 단점 |
|---|---|---|
| A. API lifespan에서 두 작업 실행 | 배포 대상 하나 | API 재시작·확장과 작업 실행이 결합되고 중복 실행 위험 |
| **B. 단일 Scheduler 컨테이너에서 두 작업 실행** | API와 장애·확장 분리, 운영 단순, 기존 Adapter 재사용 | 컨테이너와 진입점 하나 추가 |
| C. 작업별 Scheduler 컨테이너 두 개 | 작업별 독립 배포·확장 | 현재 규모에는 운영 복잡도 과다 |
| D. Celery/분산 Scheduler 도입 | 분산 락·재시도·영속 job 지원 | Broker와 운영 의존성 추가, 현재 요구 초과 |

## Decision

**B를 채택한다.** `api`와 별도의 `scheduler` 컨테이너를 둔다. Scheduler 컨테이너 하나가 뉴스 수집과 마켓 분류 작업을 등록하고 실행한다.

- `src/scheduler_main.py`는 Scheduler 프로세스의 유일한 진입점이다.
- Scheduler Adapter는 `shared_kernel/scheduler/`로 이관한다. 두 모듈이 사용하는 기술적 실행 도구이며, 어느 도메인 모듈에도 속하지 않는다.
- 각 작업은 실행마다 새 SQLAlchemy Session을 만들고 `finally`에서 닫는다.
- 작업 예외는 작업명과 함께 기록하고, 다른 작업 및 다음 tick은 계속 실행한다.
- `api`와 `scheduler`는 같은 애플리케이션 이미지를 서로 다른 명령으로 실행한다.
- stdlib asyncio Adapter와 interval 방식은 유지한다.

## Rationale

- API 요청 처리와 주기 작업은 서로 다른 수명주기와 확장 요구를 가진다.
- 작업은 두 개지만 공용 DB·환경 설정·종료 정책을 공유한다. 작업별 컨테이너 분리는 실제 독립 확장 요구가 생길 때까지 미룬다.
- Spike가 기존 Adapter의 다중 작업 실행과 독립 조립을 확인했으므로, 새 Scheduler 라이브러리 없이 전환할 수 있다.

## Reconsider When

- 작업별 서로 다른 자원·배포·확장 요구가 생기면 작업별 Worker 컨테이너로 분리한다.
- 크론 표현, misfire 복구, job 영속화가 필요하면 APScheduler를 검토한다.
- 다중 Scheduler 복제본 또는 분산 실행이 필요하면 분산 락과 queue 기반 Worker를 검토한다.
- Kubernetes 운영으로 전환하면 Kubernetes CronJob이 daemon을 대체할 수 있다.

## Migration Path

1. 공용 Scheduler Adapter와 작업 등록 함수를 추가한다.
2. `scheduler_main.py`에서 두 작업을 등록·시작·종료한다.
3. `main.py`의 lifespan Scheduler 시작을 제거한다.
4. Dockerfile과 Compose의 `api`, `scheduler` 서비스를 추가한다.
5. 기존 ADR을 이 ADR로 Superseded 처리하고 관련 Spec·Plan의 최신 설계를 갱신한다.

## References

- [기존 Scheduler ADR](./2026-07-06-scheduler-choice.md)
- [Scheduler Runtime Research](../research/scheduler-runtime.md)
- [DI·Bootstrap ADR](./2026-07-07-di-bootstrap-strategy.md)
