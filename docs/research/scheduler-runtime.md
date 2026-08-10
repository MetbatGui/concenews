# Scheduler Runtime Spike

**질문**: 뉴스 수집과 마켓 분류를 API와 분리한 단일 Scheduler 컨테이너에서 실행할 수 있는가?

## 관찰

- 로컬 Docker Engine을 사용할 수 있다.
- 기존 `AsyncioSchedulerAdapter`는 여러 비동기 작업의 등록·시작·정지·수동 실행을 지원한다.
- 뉴스 수집 조립은 환경 변수와 실행별 SQLAlchemy Session만 필요하며 HTTP 요청 수명주기에 의존하지 않는다.
- 마켓 분류 조립도 별도 SQLAlchemy Session으로 가능하다.
- 임시 독립 Python 실행에서 뉴스 작업과 추가 작업을 함께 등록하고 시작·정지했으며, 마켓 분류 서비스 조립도 성공했다.

## 결론

API와 분리된 Scheduler 컨테이너 하나가 뉴스 수집과 마켓 분류를 함께 실행할 수 있다. cron, 영속 job store, 분산 실행 요구는 아직 없으므로 기존 stdlib asyncio Adapter를 유지한다.

## 제약사항

- Scheduler replica는 하나만 실행한다. 다중 replica에는 분산 락 또는 queue 기반 실행 모델이 필요하다.
- 실제 외부 API 계약은 별도 수동 E2E에서 검증한다.

## 연결

- [Scheduler Runtime ADR](../decisions/2026-08-10-scheduler-runtime-daemon.md)
- [Scheduler Runtime Spec](../../concenews-backend/docs/spec-market-classifier-scheduler.md)
