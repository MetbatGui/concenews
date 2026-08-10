# 주기 작업 운영 계약

별도 Scheduler 프로세스·컨테이너에 적용하는 최소 운영 규약이다.

## 적용 범위

- 주기적으로 외부 API를 호출하거나 DB를 변경하는 작업
- API 서버와 독립적으로 기동되는 Worker·Scheduler 컨테이너

## 구현·검증 체크리스트

- [ ] 컨테이너는 주 프로세스 하나만 실행한다. API와 Scheduler는 같은 이미지를 쓰더라도 서로 다른 명령과 컨테이너로 실행한다.
- [ ] 필수 환경 변수나 설정이 없으면 시작 단계에서 원인과 변수명을 기록하고 비정상 종료한다.
- [ ] 작업은 이름을 가지고, 실패 시 작업명·예외 정보를 오류 로그로 남긴다.
- [ ] 한 작업의 실패가 다른 작업이나 다음 실행 주기를 중단시키지 않는다.
- [ ] 실행마다 DB Session을 만들고 성공·실패와 무관하게 닫는다.
- [ ] Scheduler는 `SIGTERM`을 받으면 새 작업 시작을 멈추고 등록 task를 정리한 뒤 종료한다.
- [ ] 단일 Scheduler replica만 실행한다. 분산 락을 도입하기 전에는 복제 실행을 금지한다.
- [ ] Integration 테스트는 Fake 외부 경계와 실제 PostgreSQL로 작업의 저장 흐름을 검증한다.
- [ ] 컨테이너 검증은 실제 외부 API 없이 Scheduler의 독립 기동·정상 종료를 확인한다.

## 책임 경계

| 항목 | 현재 책임 |
|---|---|
| 중복 실행 방지 | Compose에서 Scheduler replica 1개 유지 |
| 작업 재시도 | 다음 interval tick에서 재시도 |
| 영속 job·misfire 복구 | 현재 범위 밖 |
| 분산 락·다중 replica | 현재 범위 밖; 필요 시 별도 ADR |

## 근거

- Docker는 컨테이너의 주 프로세스에 기본적으로 `SIGTERM`을 보내고 유예 시간 후 강제 종료한다. 따라서 Scheduler는 종료 신호를 정상 처리해야 한다. [Docker 문서](https://docs.docker.com/reference/cli/docker/container/stop/)
- 컨테이너는 일반적으로 하나의 격리된 프로세스를 실행하며, 컨테이너별 책임을 분리하면 배포와 확장 경계가 명확해진다. [FastAPI 컨테이너 배포 문서](https://fastapi.tiangolo.com/deployment/docker/)
