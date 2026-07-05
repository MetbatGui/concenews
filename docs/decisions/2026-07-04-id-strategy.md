# ADR: 뉴스 도메인 ID 전략 (bigint sequence)

**Status**: Superseded by [ADR 2026-07-05 id-strategy-uuidv7](./2026-07-05-id-strategy-uuidv7.md)
**Date**: 2026-07-04
**Slice**: news-fetch

> 이 ADR 은 2026-07-05 UUID v7 재확정으로 폐기됨.
> 원문은 immutable 원칙에 따라 보존.

---

## Context

NewsItem 도메인 모델의 identity 부여 방식 결정 필요.
저장소는 초기 in-memory dict, 향후 PostgreSQL.
단일 서비스 (modular monolith).

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| UUID v4 | 분산 가능, 예측 불가 | PG B-tree page split, WAL bloat, 인덱스 밀도 79% |
| UUID v7 | 시간순 정렬, PG18+ (2025) native | 외부 dep (`uuid-utils`), 단일 서비스에서 과잉으로 판단 |
| bigint sequence | 최소 공간 (8B), 인덱스 최적, 순차 삽입 | 예측 가능, 분산 불가 |

## Decision

**bigint sequence** — `IdGenerator` (infrastructure port) 가 발급, 생성 시 필수.

- Domain: `id: int` (필수)
- Infrastructure: `IdGenerator` Protocol + `SequenceIdGenerator` impl
- 위치: `src/modules/news/infrastructure/id_generator.py` (news 로컬)
- 미래 PG: BIGSERIAL 로 impl 교체
- DTO: `id: int`

## Rationale

- 단일 서비스 monolith → 분산 ID 불필요 (당시 판단)
- 성능: bigint 인덱스 = 최적
- 공간: bigint 8B vs UUID 16B
- 인덱스 밀도: integer 97% vs UUIDv4 79% vs UUIDv7 90%
- Simple Design: 지금 필요한 최소

## Reconsider When

- 여러 writer / 마이크로서비스 분리
- Public identifier 예측 불가능성 요구 (privacy)
- PG18+ 안정화

## References

- Cybertec benchmark: UUIDv4 vs bigint
- RFC 9562 (UUIDv7)
- RFC 4122 (UUID 일반)
