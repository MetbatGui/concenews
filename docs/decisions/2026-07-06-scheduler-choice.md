# ADR: Scheduler — stdlib asyncio (초기), 로컬 news 모듈, lifespan 통합

**Status**: Accepted
**Date**: 2026-07-06
**Slice**: news-collection

---

## Context

news-collection slice 에서 15분 주기 뉴스 수집 job 필요. Scheduler 라이브러리, 위치, 실행 모델 결정.

Spike 완료: `spikes/scheduler/LEARNINGS.md` (APScheduler vs stdlib asyncio).

## Options Considered

### Library
| 옵션 | Pros | Cons |
|------|------|------|
| **A. stdlib asyncio (create_task + Event)** | 외부 dep 0, async native, 15줄 미만 | Interval 만, missed tick 복구 없음, cron 없음 |
| B. APScheduler | Cron/interval/date trigger, missed tick 복구, mature | 외부 dep, thread-based (async 통합 살짝 복잡) |
| C. Celery Beat | 분산 스케줄, worker 격리 | 무거움, Redis/RabbitMQ broker 필요 |
| D. FastAPI-scheduler wrapper | 경량 | 유지보수 활성도 낮음 |

### 위치
| 옵션 | Pros | Cons |
|------|------|------|
| **E. news 모듈 로컬** (`infrastructure/scheduler.py`) | Rule of Three 준수, YAGNI | market 모듈 스케줄 필요 시 이관 |
| F. `shared_kernel/scheduler/` | 재사용 준비 | Premature abstraction (impl 1개, 사용처 1개) |

### 실행 모델
| 옵션 | Pros | Cons |
|------|------|------|
| **G. FastAPI lifespan (same process)** | 단일 배포, 단순 | 웹 재시작 = 스케줄러 재시작 |
| H. 별도 daemon 프로세스 | 웹/스케줄러 독립 배포, MSA 준비 | 두 프로세스 관리, docker 서비스 추가 |

## Decision

**A + E + G**: stdlib asyncio, news 모듈 로컬, FastAPI lifespan 통합.

- Port: `application/ports.py` `SchedulerPort` (Protocol)
- Adapter (미래 PR): `infrastructure/scheduler.py` `AsyncioSchedulerAdapter`
- Fake (test): `FakeScheduler` (`trigger_all()` 로 수동 실행)
- FastAPI 통합: `lifespan` context manager 에서 `create_task` + `asyncio.Event` shutdown

### 이번 PR 스코프
- Port 정의만 (Adapter 는 PR #7 wire-up 에서)
- Spike LEARNINGS 유지, 스크립트 삭제
- 실 impl 없음 (Fake 는 test 필요할 때 자연 추가)

## Rationale

### Library (A - stdlib asyncio)
- **YAGNI**: 요구 = interval 1개, 15분 주기. Cron / persistence 불필요.
- **외부 dep 회피**: 지금 필요 없는 라이브러리 (APScheduler ~200KB, tzlocal 등 추가).
- **Async native**: FastAPI lifespan 과 자연 통합, `run_in_executor` 우회 불필요.
- **Port abstraction**: 실 impl 교체 자유. 미래 APScheduler 필요 시 Adapter 만 교체.

### 위치 (E - news 로컬)
- **Rule of Three**: news 모듈만 사용 → shared_kernel 은 premature.
- **IdGenerator 사례와 일관** (ADR 2026-07-05-id-strategy-uuidv7).
- **이관 비용 낮음**: market/matching 스케줄 등장 시 5분 작업.

### 실행 모델 (G - lifespan)
- **단일 프로세스 monolith 정합**: news-collection 은 아직 monolith 스코프.
- **배포 단순**: 하나의 docker 서비스, 하나의 entry point.
- **미래 별도 프로세스**: 트래픽 / 배포 격리 필요 시 lifespan → 별도 daemon 로 이전.

## Reconsider When

### Library
- Cron 표현 필요 (매 정각 등) → APScheduler
- Missed tick 복구 → APScheduler (misfire_grace_time)
- 다중 job (news + market + matching) → APScheduler (job store)
- 분산 스케줄 → Celery Beat

### 위치
- 두 번째 모듈 (market 등) 스케줄 필요 → `shared_kernel/scheduler/`

### 실행 모델
- 웹 트래픽 부담 → 스케줄러 분리 (별도 daemon)
- 스케줄러 crash 시 웹까지 영향 → 격리 (별도 프로세스)
- Kubernetes CronJob 활용 → daemon 아예 삭제, k8s 스케줄

## Migration Path (미래)

### stdlib → APScheduler
- Adapter 교체 (`SchedulerPort` interface 유지)
- Dep 추가: `apscheduler`
- Lifespan 코드 조정 (BackgroundScheduler.start/shutdown)
- 예상 churn: 30분

### news 로컬 → shared_kernel
- 파일 이동 (`mv`), import 갱신
- 예상 churn: 10분

### Lifespan → 별도 daemon
- `src/scheduler_main.py` 신규 (entry point)
- Dockerfile / docker-compose 서비스 추가
- 예상 churn: 1시간

## References

- Spike LEARNINGS: `concenews-backend/spikes/scheduler/LEARNINGS.md`
- FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/
- 관련: [ADR 2026-07-05 id-strategy-uuidv7](./2026-07-05-id-strategy-uuidv7.md) (Rule of Three)
- 관련: [ADR 2026-07-06 db-library](./2026-07-06-db-library.md) (sync 채택 근거와 동일 스케일 판단)
