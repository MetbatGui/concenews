# Container Scheduler Smoke 검증

**날짜**: 2026-08-10
**관련 Slice**: scheduler-runtime

## 질문

실제 TheNewsAPI·Polymarket 호출 없이, 동일 백엔드 이미지로 실행되는 API와 Scheduler 컨테이너의 기동·종료 경계를 어떻게 검증하는가?

## 확인 결과

- `migrate`·`api`·`scheduler` 서비스는 하나의 `concenews-backend:local` 이미지를 서로 다른 명령으로 실행할 수 있다.
- `migrate`가 PostgreSQL healthcheck 뒤 완료되어야 API와 Scheduler가 시작되도록 Compose 의존성을 둘 수 있다.
- API는 migration 뒤 `/health` 응답으로 기동을 확인한다.
- Scheduler smoke는 외부 API·DB를 호출하지 않는 Fake 작업 두 개를 실제 `AsyncioSchedulerAdapter`에 등록한다. `network_mode: none`은 추가 방어 계층으로 유지한다.
- Fake 작업이 등록·시작되면 readiness 파일을 만들고, smoke는 이 파일을 제한 시간 안에 확인한 뒤 SIGTERM을 보낸다.

## 적용

`just check-container`는 이미지 build, PostgreSQL·migration·API healthcheck, Fake 작업 Scheduler의 readiness·SIGTERM 종료를 차례로 검증한다.

## 후속 조건

운영 Scheduler에 health endpoint가 생기면, smoke의 파일 readiness를 해당 healthcheck로 교체할 수 있다.
