# ADR: Spike 는 unknown 만날 때 on-demand

**Status**: Accepted
**Date**: 2026-07-05
**Slice**: Cross-cutting (프로세스)

---

## Context

Slice 진행 중 여러 기술 unknown 이 동시에 존재 가능 (DB, scheduler, 외부 API 등).
Spike 를 언제 실행할지 두 가지 접근:

1. **Batch spike**: slice 시작 전 모든 unknown 을 한번에 검증
2. **On-demand spike**: slice 진행 중 unknown 을 만날 때마다 즉시 spike

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| Batch (모아서) | Comparison 편함, context switching 감소 | BDUF 냄새, 안 쓰는 것도 학습, 미래 예측 실패 시 재작업 |
| **On-demand (필요할 때)** | JIT learning, YAGNI 준수, 결정 시점 = 지금 확정 | Context switch (하지만 slice 진행 중 자연스러움) |

## Decision

**On-demand spike**.

Slice 진행 중 unknown 을 만나면 즉시:
```
[unknown 발견]
   ↓
spikes/{topic}/ 폴더 생성
   ↓
학습 (LEARNINGS.md)
   ↓
결정 → trigger 매칭 시 ADR 작성
   ↓
Docs (spec/plan) 갱신
   ↓
Spike 폴더 삭제 (LEARNINGS.md 는 유지)
   ↓
Implement
```

**한 unknown = 한 spike = (필요시) 한 ADR = 한 PR**.

## Rationale

- **XP just-in-time learning 정신**: 지금 필요한 것만 학습
- **YAGNI**: 안 쓰는 것 미리 검증 안 함
- **결정 신선도**: unknown 만난 순간이 학습 최고 시점 (context 명확)
- **Waste 방지**: batch 시 slice 방향 변경 시 spike 결과 폐기
- **BDUF 회피**: 미래 예측 대신 실행 중 발견

## Reconsider When

- 여러 unknown 이 강하게 상호 의존 (예: DB choice 가 scheduler choice 를 규정) → 병행 spike 정당화
- 큰 아키텍처 전환 (예: monolith → microservices) → 사전 종합 spike 필요할 수도

## Spike vs ADR 관계

- Spike = 로컬 학습 (git commit X, 삭제)
- ADR = 결정 로그 (spike 결과가 [ADR-process trigger](../adr-process.md) 매칭 시 작성)
- 모든 spike 가 ADR 로 이어지지 않음 (trivial 학습은 spec/plan 갱신만)

## Migration Path

기존 spike-process 는 유지 (라이프사이클/규칙 그대로).
"언제 spike 를 시작하나?" 에 답만 명시 (on-demand).

## References

- [spike-process.md](../../concenews-backend/docs/spike-process.md) — spike 라이프사이클
- [adr-process.md](../adr-process.md) — ADR trigger
- XP 원칙: [xp.md](../architecture/principles/xp.md)
