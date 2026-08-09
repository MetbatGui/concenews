# ADR: GitHub 작업 단위 모델 통일

**Status**: Accepted
**Date**: 2026-08-10
**Slice**: Cross-cutting

## Context

개발 워크플로우와 GitHub 전략 문서가 Epic, Slice, Issue, Milestone, Task의 관계를 서로 다르게 정의한다. 실제 저장소에는 Market Bounded Context Epic 아래에 market-classification Slice Issue가 존재하므로, 문서 불일치를 제거해야 한다.

## Options Considered

| 옵션 | 장점 | 단점 |
|------|------|------|
| Milestone을 Slice로 사용 | 기능별 GitHub 묶음이 단순하다 | 릴리스 단위 추적이 불명확해진다 |
| Milestone을 릴리스로 사용 | GitHub 기본 의미와 배포 단위가 일치한다 | Slice 진행은 Issue 관계로 추적해야 한다 |

## Decision

다음 모델을 프로젝트의 단일 작업 단위 모델로 채택한다.

| 단위 | 의미 | GitHub 표현 |
|------|------|-------------|
| Epic | Bounded Context | 상위 Issue |
| Slice | 사용자 가치가 있는 수직 기능 | Epic의 하위 Issue |
| Task | Slice를 완성하는 작고 독립된 변경 | PR 하나 |
| Milestone | 릴리스 버전 | Milestone |

- 기준 브랜치는 실제 저장소와 같은 `master`다.
- 개발 브랜치는 `feature/{slice}-{task}` 형식이다.
- Slice의 마지막 PR만 `Closes #{slice-issue}`를 사용한다. 그 외 PR은 `Related to #{slice-issue}`를 사용한다.
- Task 목록은 별도 `docs/tasks.md`를 만들지 않고 해당 Slice의 `plan-{slice}.md`에 유지한다.

## Rationale

실제 GitHub 구조와 문서 모델을 일치시키면 진행 상태와 릴리스 범위를 모두 한 번에 이해할 수 있다. 1인 개발에서는 Task를 별도 Issue로 쪼개는 관리 비용보다 Plan의 체크리스트와 작은 PR 조합이 더 단순하다.

## Reconsider When

- 여러 개발자가 병렬로 같은 Slice의 Task를 맡게 될 때
- 릴리스와 Slice의 관계가 일대일로 고정되어 Milestone의 릴리스 의미가 사라질 때

## References

- [개발 워크플로우](../workflow.md)
- [GitHub 전략](../github-strategy.md)
- [Vertical Slice 원칙](../architecture/principles/vertical-slices.md)
