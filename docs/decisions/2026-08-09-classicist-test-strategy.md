# ADR: Classicist 테스트 전략과 E2E 경계

**Status**: Accepted
**Date**: 2026-08-09
**Slice**: Cross-cutting

## Context

프로젝트의 테스트는 실제 PostgreSQL, 상태를 가진 Fake, HTTP mock을 함께 사용한다. 그러나 실제 외부 API 호출 테스트에 E2E 마커가 없고, 실제 DB와 외부 API mock을 조합한 Integration 테스트가 `*_e2e.py`로 명명되어 테스트 계층의 의미가 혼재되어 있다.

병합 전 품질 게이트는 빠르고 결정적이어야 하며, 네트워크·외부 API 상태·비용에 영향을 받으면 안 된다.

## Options Considered

| 옵션 | 장점 | 단점 |
|------|------|------|
| Mockist 중심 | 각 협력자를 독립적으로 제어하기 쉽다 | 구현 상호작용에 결합되고 리팩터링 비용이 커진다 |
| Classicist + 외부 경계 대체 | 실제 객체 조합과 관찰 가능한 결과를 검증한다 | 통합 테스트 환경을 준비해야 한다 |
| 모든 테스트에서 실제 외부 API 호출 | 운영 환경과 가장 유사하다 | 느리고 비결정적이며 비용·rate limit 영향을 받는다 |

## Decision

Classicist 전략을 채택한다.

- Domain, Application, Repository는 가능한 실제 구현체를 조합하고 결과 상태·반환값을 검증한다.
- 상태를 갖는 단순 Fake는 외부 의존성을 대체하는 경우에만 허용한다. 내부 호출 횟수·호출 순서 검증은 외부 프로토콜 계약일 때만 사용한다.
- PostgreSQL은 Integration 테스트에서 실제 컨테이너를 사용한다.
- HTTP, 시간, 스케줄러처럼 프로세스 밖 경계는 결정적 Transport/Fake로 대체한다.
- 실제 외부 API와 실제 DB를 함께 사용하는 테스트만 `e2e` 마커를 붙인다. 이는 `just check-e2e`로 수동 실행하며 `check-branch-green`에는 포함하지 않는다.
- 외부 API mock 응답은 Spike에서 확인한 형식을 기반으로 `tests/fixtures/`의 버전 관리 fixture를 단일 진실원천으로 사용한다.

## Rationale

실제 객체 조합은 테스트가 구현 세부 대신 사용자에게 보이는 결과와 상태를 보호하게 한다. 외부 경계만 대체하면 병합 전 검증은 빠르고 재현 가능하게 유지하면서도 실제 데이터베이스·마이그레이션 문제를 조기에 발견할 수 있다.

## Reconsider When

- PostgreSQL 기반 Integration 테스트가 개발 피드백 속도를 지속적으로 해칠 때
- 외부 API 제공자가 공식 sandbox 또는 계약 검증 환경을 제공할 때
- 테스트 대상이 여러 독립 프로세스로 분리되어 현재의 경계 정의가 부정확해질 때

## Migration Path

1. 실제 외부 API 테스트에 `e2e` 마커를 부여한다.
2. 외부 API mock을 사용하는 실제 DB 테스트의 파일명을 `*_integration.py`로 변경한다.
3. 병합 전 게이트는 `not e2e`만 실행하고, E2E는 별도 Just 작업으로 제공한다.
4. 기존 hand-written API mock을 버전 관리 fixture로 이관한다.

## References

- [테스트 규약](../../concenews-backend/docs/conventions/testing.md)
- [XP 원칙](../architecture/principles/xp.md)
- [ADR 프로세스](../adr-process.md)
