# Container Scheduler Smoke 검증

**날짜**: 2026-08-10
**관련 Slice**: scheduler-runtime

## 질문

실제 TheNewsAPI·Polymarket 호출 없이, 동일 백엔드 이미지로 실행되는 API와 Scheduler 컨테이너의 기동·종료 경계를 어떻게 검증하는가?

## 확인 결과

- `migrate`·`api`·`scheduler` 서비스는 하나의 `concenews-backend:local` 이미지를 서로 다른 명령으로 실행할 수 있다.
- `migrate`가 PostgreSQL healthcheck 뒤 완료되어야 API와 Scheduler가 시작되도록 Compose 의존성을 둘 수 있다.
- API는 migration 뒤 `/health` 응답으로 기동을 확인한다.
- Scheduler smoke에서는 `network_mode: none`으로 외부 네트워크를 차단하고, 더미 토큰으로 조립만 통과시킨다. 작업 실행 중 네트워크 오류는 Scheduler의 작업별 예외 격리 대상이며, 실제 외부 API 호출은 발생하지 않는다.
- Scheduler 시작 직후 종료 signal handler 준비에 시간이 필요하므로, smoke는 5초 뒤 SIGTERM을 보내고 정상 종료 코드를 확인한다.

## 적용

`just check-container`는 이미지 build, PostgreSQL·migration·API healthcheck, 네트워크 차단 Scheduler의 SIGTERM 종료를 차례로 검증한다.

## 후속 조건

Scheduler에 명시적 readiness 신호 또는 health endpoint가 생기면, 고정 5초 대기 대신 readiness 기반으로 smoke 종료 시점을 바꾼다.
