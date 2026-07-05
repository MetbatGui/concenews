# Scheduler Spike: Learnings & Decision

## Question
FastAPI lifespan 안에서 정기 job (interval trigger) 실행 방법?
APScheduler (외부 dep) vs stdlib asyncio (dep 0)

## Environment
- Python 3.13
- FastAPI (lifespan async)
- 요구: 15분 간격 단일 job (news collection)

## Candidates Tested

### 1. APScheduler (BackgroundScheduler)
- Interval trigger 자연
- 3.5초 내 3 ticks (t=1, 2, 3)
- Thread-based → sync job 자연, async job 도 지원 (AsyncIOScheduler)
- Shutdown clean
- Cron / date / interval 다양

### 2. stdlib asyncio (create_task + Event)
- 15줄 미만 커스텀 구현
- 3.5초 내 4 ticks (t=0, 1, 2, 3, 즉시 실행)
- 완전 async, FastAPI 정합
- Interval 만 지원 (cron 필요 시 별도 구현)
- Persistence 없음

---

## Trade-off

| 관점 | APScheduler | stdlib asyncio |
|------|-------------|----------------|
| 외부 dep | +apscheduler, tzlocal | 없음 |
| 코드 라인 | 앱 5줄 | 앱 15줄 |
| Trigger 다양성 | interval / cron / date | interval 만 |
| Job persistence | Memory / DB / Redis | 없음 |
| 실행 모델 | Thread (default) / async 옵션 | Async native |
| 학습 곡선 | 낮음 (관용 API) | 최저 (stdlib) |
| Test 격리 | Fake port 로 우회 | Fake port 로 우회 |
| Missed tick 복구 | 있음 (misfire policy) | 없음 (다음 tick 대기) |
| Portfolio 신호 | "real library 사용" | "lean, no dep" |

---

## Decision: **stdlib asyncio** (초기), APScheduler 는 트리거 시 이관

### Why
- **YAGNI**: 요구 = interval 1개, 15분 주기. Cron / persistence 불필요.
- **외부 dep 회피**: 지금 필요 없는 라이브러리.
- **Async native**: FastAPI lifespan 과 자연 통합 (`asyncio.create_task`).
- **Fake port 로 test 격리**: 어차피 SchedulerPort abstraction 이므로 impl 은 후일 교체 가능.

### Reconsider Triggers (APScheduler 로 이관 시점)
- Cron 표현 필요 (매 15분 정각 등)
- Missed tick 복구 필요 (컨테이너 재시작 후 특정 시각 정확히 실행 등)
- Multiple job (news + market + matching 등)
- Job persistence (DB backed queue)

### Implementation Notes
- Port: `application/ports.py` `SchedulerPort` Protocol
- Adapter (미래 PR #7): `infrastructure/scheduler.py` `AsyncioSchedulerAdapter`
- Fake (test): `FakeScheduler` with `trigger_all()` 로 수동 실행
- FastAPI 통합: `lifespan` 에서 `create_task` + `Event` 로 shutdown 제어

---

## References
- APScheduler docs: https://apscheduler.readthedocs.io/
- FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/
- Spike 결정 프로세스: docs/adr-process.md
