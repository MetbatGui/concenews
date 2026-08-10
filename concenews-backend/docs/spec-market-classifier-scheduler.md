# Spec: Scheduler Runtime 분리

**상태**: Accepted
**Slice**: `scheduler-runtime`
**관련 결정**: [Scheduler Runtime ADR](../../docs/decisions/2026-08-10-scheduler-runtime-daemon.md)
**운영 규약**: [주기 작업 운영 계약](conventions/scheduled-workloads.md)

---

## 배경

`NewsCollectorService`와 `MarketClassifierService.run()`은 실제 수집·분류 흐름을 이미 수행한다. 그러나 현재 앱의 lifespan은 뉴스 수집 작업만 API 프로세스 안에서 등록한다. 마켓 분류는 자동 실행되지 않고, API 재시작·확장과 뉴스 수집 실행이 결합되어 있다.

이 Slice는 도메인 규칙이나 수집·분류 로직을 바꾸지 않는다. 두 작업을 API와 분리된 Scheduler 컨테이너에서 안전하게 실행하도록 런타임 경계를 전환한다.

## 사용자 스토리

> 시스템은 API 요청 처리와 무관하게 뉴스 수집과 활성 Polymarket 마켓 분류를 주기적으로 실행하여, 이후 조회·연결 기능에 사용할 최신 데이터를 유지한다.

## 범위

### 포함

- 별도 Scheduler 진입점과 `scheduler` 컨테이너
- 뉴스 수집과 마켓 분류의 작업 등록
- `NEWS_COLLECTOR_INTERVAL`(기본 900초), `MARKET_CLASSIFIER_INTERVAL`(기본 300초)
- 매 tick마다 새 SQLAlchemy Session으로 서비스 조립·실행·정리
- API와 Scheduler의 독립 시작·종료 검증
- 작업별 실패 격리와 오류 기록
- `api`·`scheduler`·`postgres` Compose 구성
- [주기 작업 운영 계약](conventions/scheduled-workloads.md)의 체크리스트 충족

### 제외

- 마켓 가격·거래량 스냅샷 수집
- 마켓 조회 API 엔드포인트
- 분류 규칙 또는 태그 ID 변경
- 작업별 별도 Worker 컨테이너, 분산 스케줄러, 분산 락
- cron 표현, job 영속화, 재시도 정책 고도화

## Acceptance Criteria

### AC1. API와 Scheduler 실행 경계

- API는 HTTP 라우터만 기동하며 Scheduler 작업을 등록·시작하지 않는다.
- `scheduler_main.py`는 뉴스 수집과 마켓 분류를 하나의 `AsyncioSchedulerAdapter`에 등록하고 한 번만 시작·정지한다.
- Scheduler는 SIGTERM 또는 KeyboardInterrupt에서 등록 작업을 정리하고 종료한다.

### AC2. 실행 주기

- 뉴스 수집은 `NEWS_COLLECTOR_INTERVAL`이 없으면 900초를 사용한다.
- `MARKET_CLASSIFIER_INTERVAL`이 없으면 300초를 사용한다.
- 각 환경 변수가 있으면 해당 정수 초 값을 사용한다.
- 수동 trigger는 등록된 두 작업을 각각 한 번 실행할 수 있다.

### AC3. 세션 생명주기

- 매 실행은 새 Session을 만들고, 성공·실패와 무관하게 닫는다.
- `NewsCollectorService`와 `MarketClassifierService`는 각 모듈의 bootstrap 함수로 조립한다.

### AC4. 실패 격리

- 각 작업의 예외는 작업명과 함께 오류 로그로 남긴다.
- 한 tick의 실패는 Scheduler·다른 작업·다음 tick을 중단하지 않는다.

### AC5. 검증

- Integration 테스트는 수동 trigger 후 Fake 외부 경계와 실제 PostgreSQL을 사용해 각 작업의 저장 흐름을 검증한다.
- 두 작업 등록, 시작·정지, API가 Scheduler를 시작하지 않음을 검증한다.
- 컨테이너 수준 검증은 실제 외부 API 호출 없이 Scheduler 프로세스가 기동·종료하는지 확인한다.
- `just check-branch-green`이 통과한다.

## 설계 제약

- `AsyncioSchedulerAdapter`는 두 모듈이 사용하는 기술적 실행 도구이므로 shared kernel에 둔다.
- Scheduler 진입점만 두 모듈의 bootstrap을 알아도 된다. 모듈끼리 상대 모듈의 내부 구현을 import하지 않는다.
- 5분 주기는 환경 변수로 조정 가능하되, 분류 결과의 DB 캐시와 `end_date` 만료 규칙은 변경하지 않는다.

## 완료 조건

- API와 Scheduler가 별도 컨테이너·명령으로 기동된다.
- Scheduler가 뉴스 수집(기본 900초)과 마켓 분류(기본 300초)를 등록한다.
- 작업 예외가 로그로 남고 이후 tick과 다른 작업이 계속된다.
- Integration 테스트와 로컬 품질 게이트가 녹색이다.

## 참고

- [매크로 마켓 분류 Spec](spec-market-tracking.md)
- [매크로 마켓 분류 Plan](plan-market-tracking.md) — PR #6
- [스케줄러 선택 ADR](../../docs/decisions/2026-07-06-scheduler-choice.md)
- [DI·Bootstrap ADR](../../docs/decisions/2026-07-07-di-bootstrap-strategy.md)
