# ADR: DB 라이브러리 — SQLAlchemy 2.0 sync + psycopg + Alembic

**Status**: Accepted
**Date**: 2026-07-06
**Slice**: news-collection (shared kernel)

---

## Context

News-collection slice 에서 DB 도입 필요 (뉴스 영구 저장, `link` unique dedup).
Shared kernel 로 배치 예정 (`src/shared_kernel/db/`).

라이브러리 선택 기준:
- FastAPI 통합 자연스러움
- Alembic migration
- 개발 편의 (Windows dev 환경)
- 미래 MSA 전환 대응

Spike 완료: `spikes/db/LEARNINGS.md`.

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| **A. SQLAlchemy 2.0 sync + psycopg** | 표준 코드, Windows 문제 없음, Alembic 심플 | 미래 async 전환 시 rewrite 필요 |
| B. SQLAlchemy 2.0 async + psycopg | Async 준비 | Windows `SelectorEventLoop` 강제, 복잡도 |
| C. SQLAlchemy 2.0 async + asyncpg | 최상 성능, Windows OK | Alembic async engine 우회 셋업 필요, 복잡도 |
| D. Django ORM 등 | — | 스택 불일치 |

## Decision

**A: SQLAlchemy 2.0 sync + psycopg + Alembic**.

- Engine: `create_engine(dsn, pool_pre_ping=True)`
- Session: `Session(engine)` context manager
- Alembic: sync env.py, `alembic revision --autogenerate`
- DSN 환경 변수: `DATABASE_URL`

## Rationale

- **Portfolio 스케일 = sync 충분**: DB I/O 부하 크지 않음, 성능 이슈 없음.
- **복잡도 최소화**: async 는 await 전파, event loop 정책, Windows 이슈 등 부수 관리 증가.
- **FastAPI 통합**: `def` endpoint + threadpool 로 동시성 확보. Async endpoint 도 sync SQLAlchemy 호출 가능.
- **Alembic 표준 셋업**: async engine 대비 우회 없이 자연 사용.
- **미래 MSA 전환 대응**: sync → async 이전은 rewrite 필요하나 규모 관리 가능 (뉴스 모듈 규모 4~6시간 추정). 지금 async 로 복잡도 감내 vs 미래 이전 비용 = 후자가 낫다는 판단.

## Reconsider When

- **모듈간 network 호출 급증** (MSA 실제 전환) → async + asyncpg 재검토
- **DB I/O 병목 실측** (수천 concurrent connection) → async 필요성 재검토
- **팀 확장**: async 표준 팀 합류 시 사전 대응

## Migration Path (미래 async 전환 시)

**Trigger**: MSA 분리 실행 or I/O 병목 실측.

**변경 범위**:
- 라이브러리: psycopg → asyncpg (Windows 이슈 회피)
- Engine: `create_engine` → `create_async_engine`
- Session: `Session` → `AsyncSession`
- Repository 메서드: sync → `async def` + `await`
- Bootstrap DI: 동일 (팩토리만 async 반환)
- Endpoint: `def` → `async def`
- Alembic: 별도 sync engine 통해 migration 실행 (env.py 조정)

**Estimated churn** (뉴스 모듈 기준): 4~6시간.
**전체 slice 규모 확대 시**: 지수 증가 → MSA 결정 시 즉시 이전 권장.

## References

- Spike LEARNINGS: `concenews-backend/spikes/db/LEARNINGS.md`
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/en/20/
- psycopg 3: https://www.psycopg.org/psycopg3/docs/
- Alembic: https://alembic.sqlalchemy.org/
- 관련: [ADR 2026-07-05 timezone-policy](./2026-07-05-timezone-policy.md) (TIMESTAMPTZ 사용)
