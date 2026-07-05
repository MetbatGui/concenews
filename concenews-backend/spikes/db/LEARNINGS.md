# DB 라이브러리 Spike: Learnings & Decision

## Question
SQLAlchemy 2.0 sync vs async? Alembic 셋업은?

## Environment
- Python 3.13, Windows
- PG 17 (Docker: `postgres:17-alpine`)
- SQLAlchemy 2.0.51, psycopg 3.3.4, Alembic 1.18.5

## Candidates Tested
1. Sync (`create_engine` + `Session`)
2. Async (`create_async_engine` + `AsyncSession`)
3. Alembic init 확인

---

## Findings

### Sync SQLAlchemy 2.0
- DSN: `postgresql+psycopg://user:pass@host:port/db`
- Session context manager 자연 (`with Session(engine) as session:`)
- ORM 모델 정의 간결 (`Mapped[T]`, `mapped_column`)
- `select().scalars().all()` 표준 쿼리
- **에러 없음. 표준 코드로 작동.**

### Async SQLAlchemy 2.0
- DSN: `postgresql+psycopg_async://...` (별도 dialect)
- `AsyncSession`, `create_async_engine`, `async with`
- 🔴 **Windows 이슈**: 기본 `ProactorEventLoop` 사용 시 `InterfaceError`
  ```
  Psycopg cannot use the 'ProactorEventLoop' to run in async mode.
  ```
- **Fix**: `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())`
- FastAPI 사용 시에도 동일 정책 필요할 수 있음 (uvicorn 이 자동 처리하는지 확인 필요)
- 코드 복잡도: `await` 곳곳, `run_sync` 로 metadata 조작 등

### Alembic
- `alembic init <dir>` → env.py, alembic.ini, script.py.mako, versions/ 생성
- **Sync/async 모두 지원** (env.py 커스터마이징으로)
- Async env.py: `context.run_migrations_online` 을 async 로 래핑
- Autogenerate: `alembic revision --autogenerate -m "msg"` — 모델 diff 로 migration 자동 생성

---

## Trade-off 정리

| 관점 | Sync | Async |
|------|------|-------|
| API 표면 복잡도 | 낮음 (context manager 표준) | 높음 (await, event loop 정책 관리) |
| Windows 호환 | ✅ 문제 없음 | ⚠️ SelectorEventLoop 강제 필요 |
| FastAPI 통합 | `def` endpoint + threadpool (기본) | `async def` endpoint 자연 |
| Performance | 충분 (portfolio 스케일) | 이론적 우세 (I/O bound 큰 부하 시) |
| ORM 사용감 | 표준 | Async 곳곳 |
| Alembic | 쉬움 | env.py 커스텀 필요 |
| 학습 곡선 | 낮음 | 중 |

---

## Decision: **Sync SQLAlchemy 2.0**

### Why
- **Portfolio 스케일 = sync 충분**: DB 부하 크지 않음. 성능 이슈 없음.
- **복잡도 최소화**: async 는 await + event loop 정책 + Windows 이슈 → 부수 관리 증가.
- **FastAPI 통합**: `def` endpoint + threadpool 로 동시성 확보 (async endpoint 도 sync SQLAlchemy 호출 가능).
- **Alembic 심플**: sync env.py 표준.
- **Migration path**: 미래 async 필요 시 이전 가능 (SQLAlchemy 는 동일 ORM 사용, `AsyncSession` 만 도입).

### Implementation Notes
- DSN: `postgresql+psycopg://concenews:concenews@localhost:5432/concenews`
- Engine: `create_engine(dsn, echo=<config>, pool_pre_ping=True)`
- Session: `Session(engine)` context manager
- Test 격리: transaction rollback fixture (savepoint 기반)
- `pool_pre_ping=True` 로 stale connection 자동 감지

### Alembic 셋업 계획
- `alembic init alembic/` (프로젝트 루트)
- `env.py` 에 `target_metadata = Base.metadata` 설정
- DSN 은 환경 변수 (`DATABASE_URL`)
- `alembic revision --autogenerate` 사용
- 초기 migration = news 테이블 (PR #3)

---

## References
- SQLAlchemy 2.0 docs: https://docs.sqlalchemy.org/en/20/
- psycopg 3 docs: https://www.psycopg.org/psycopg3/docs/
- Alembic docs: https://alembic.sqlalchemy.org/
- Windows async 이슈: https://sqlalche.me/e/20/rvf5
