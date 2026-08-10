# ADR: Spike 학습 결과의 리포 기록

**Status**: Accepted
**Date**: 2026-08-10
**Slice**: Cross-cutting

---

## Context

기존 Spike 규약은 임시 코드와 `LEARNINGS.md`를 로컬에 두고 커밋하지 않도록 했다. 그러나 프로젝트의 최상위 지식 저장 정책은 모든 학습·규칙·결정을 리포 문서에 기록하도록 요구한다. 로컬 학습 기록은 다른 에이전트와 다음 세션에서 참조할 수 없고, ADR·Spec에서 끊어진 링크가 될 수 있다.

## Options Considered

| 옵션 | 장점 | 단점 |
|---|---|---|
| 학습 기록까지 로컬 유지 | Spike 폴더가 가벼움 | 지식 SSOT 위반, 재현·참조 불가 |
| **임시 코드만 로컬 유지하고 학습 결과를 `docs/research/`에 기록** | 학습의 이식성·추적성 확보 | 짧은 Markdown 문서 관리 필요 |
| Spike 코드와 결과를 모두 커밋 | 재현 코드 보존 | 실험 코드가 프로덕션 리포를 오염 |

## Decision

- `spikes/{topic}/`의 임시 실행 코드는 로컬 전용이며 커밋하지 않고 삭제한다.
- 질문, 관찰, 선택지, 결론, 제약사항은 `docs/research/{topic}.md`에 기록하고 커밋한다.
- 설계 결정이면 해당 ADR은 Research 문서를 참조하고, Spec·Plan은 채택 결과를 링크한다.
- 사소한 확인도 이후 테스트 fixture·구현 계약에 영향을 주면 Research 문서에 남긴다.

## Rationale

학습의 가치는 실험 스크립트가 아니라 재현 가능한 발견과 그로부터 나온 결정에 있다. 코드 폐기는 리포를 정결하게 유지하고, 결과 문서의 커밋은 Codex·Claude·사람 사이의 SSOT를 보장한다.

## Reconsider When

- 성능 benchmark나 호환성 검증을 지속 반복해야 해 재실행 코드 자체가 제품 자산이 될 때
- 외부 서비스의 이용 약관상 응답 예시를 리포에 기록할 수 없을 때

## References

- [기존 On-demand Spike ADR](./2026-07-05-on-demand-spike.md)
- [ADR 프로세스](../adr-process.md)
- [지식 저장 정책](../../AGENTS.md)
