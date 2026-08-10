# ADR: 개발 워크플로우 실행 계약 명확화

**Status**: Accepted
**Date**: 2026-08-10
**Slice**: Cross-cutting

---

## Context

프로젝트에는 Spec-Kit 기반 개발 플로우와 ADR-first 규칙이 각각 존재하지만, 설계 결정이 필요한 작업에서 ADR·Spec의 선후 관계와 Task·PR·브랜치의 대응이 한눈에 드러나지 않았다. 별도 Scheduler 컨테이너처럼 운영 경계가 추가되는 작업은 기능 검증뿐 아니라 종료·중복 실행·환경 설정의 운영 계약도 필요하다.

## Options Considered

| 옵션 | 장점 | 단점 |
|---|---|---|
| 기존 문서별 표현 유지 | 문서 변경 없음 | 실행 순서와 책임이 해석에 의존 |
| **표준 순서·PR 경계·운영 체크리스트 명시** | 작업 시작·검토 기준이 일관됨 | 짧은 문서 유지 비용 발생 |

## Decision

다음 계약을 프로젝트 표준으로 명시한다.

1. `기획 → Spike(필요 시) → ADR(설계 결정 시) → Spec → Plan → 사용자 검토 → Task/브랜치 → TDD 구현 → 품질 게이트 → PR`
2. 구현 Task 하나는 PR 하나이며, PR 하나는 `feature/{slice}-{task}` 브랜치 하나를 사용한다.
3. 별도 프로세스·컨테이너 작업은 환경 설정 실패, 작업별 로그, 정상 종료, 독립 기동, 중복 실행 책임을 Acceptance Criteria와 검증에 포함한다.

## Rationale

- ADR은 결정의 이유를 먼저 고정하고, Spec·Plan은 그 결정을 실행 가능한 최신 상태로 표현한다.
- 브랜치와 PR을 1:1로 두면 리뷰 범위와 master green 규칙이 명확해진다.
- 컨테이너의 주 프로세스는 종료 신호를 받으므로 graceful shutdown은 기능이 아니라 실행 계약이다.

## Reconsider When

- 병렬 개발 또는 장기 릴리스 브랜치가 필요해 1 Task = 1 PR 규칙이 작업 비용을 과도하게 높일 때
- 운영 환경이 Docker Compose에서 Kubernetes 등으로 바뀌어 별도 운영 계약이 필요할 때

## References

- [개발 플로우](../workflow.md)
- [Git Workflow](../git-workflow.md)
- [Docker 컨테이너 종료 신호](https://docs.docker.com/reference/cli/docker/container/stop/)
- [FastAPI 컨테이너 배포](https://fastapi.tiangolo.com/deployment/docker/)
