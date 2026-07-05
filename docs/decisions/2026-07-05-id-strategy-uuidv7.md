# ADR: 뉴스 도메인 ID 전략 — UUID v7 재확정

**Status**: Accepted
**Date**: 2026-07-05
**Slice**: news-fetch
**Supersedes**: [ADR 2026-07-04 id-strategy](./2026-07-04-id-strategy.md) (bigint sequence)

---

## Context

이전 결정 ([2026-07-04 bigint sequence](./2026-07-04-id-strategy.md)) 후 재고 결과 UUID v7 로 전환.

**폐기 이유**:
- Public URL (`/news/1`, `/news/2`) 순차 노출 = 정보 은닉 부족 (crawling, enumeration 취약).
- 미래 마이크로서비스 분리 시 bigint counter 조정 필요, UUID v7 은 자동.
- 뉴스 규모 (수백~수천 건) 에서 bigint 성능 이점 무의미.
- PG18+ (2025) UUIDv7 native 지원 확정 → 조기 채택 리스크 낮음.

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| UUID v4 | 분산 가능, 예측 불가, stdlib | PG B-tree page split, WAL bloat, 인덱스 밀도 79% |
| **UUID v7** | 시간순 정렬, PG 인덱스 90%, PG18+ (2025) native | 외부 dep (`uuid-utils` 지금), Python stdlib 미포함 |
| bigint sequence | 최소 공간 (8B), 인덱스 97% | Public URL 예측 가능, 분산 불가 |

## Decision

**UUID v7** — `IdGenerator` (application port) 가 발급, 생성 시 필수.

- Domain: `id: UUID` (필수)
- Application: `ports.py` — `IdGenerator` Protocol
- Infrastructure: `id_generator.py` — `UuidV7Generator` (`uuid_utils.compat.uuid7`)
- Port/Adapter 분리: Hexagonal architecture 준수 (Port 는 안쪽 application, Adapter 는 바깥쪽 infrastructure)
- 위치: `src/modules/news/` (news 로컬)
  - Rule of Three: 두 번째 모듈 필요 시 `src/shared_kernel/` 로 이전
- 미래 PG: `UUID PRIMARY KEY DEFAULT uuidv7()` (PG18+ native)
- Repository: 순수 저장
- DTO: `id: UUID` (JSON 직렬화 시 string)

**Usage**:
```python
item = NewsItem(id=id_gen.generate(), title=..., link=..., ...)
repo.save(item)
```

## Rationale

- **시간순 정렬**: v7 앞 48비트 timestamp. `published_at` 정렬과 자연 정합.
- **PG 인덱스 friendly**: v7 밀도 90% vs v4 79%. 순차성으로 page split 완화.
- **분산 대응**: 미래 마이크로서비스 분리 시 collision-free 자연.
- **Public identifier**: URL 노출 시 sequential 예측 불가 (bigint 대비 정보 은닉).
- **PG18+ native**: 2025 정식 지원.
- **DDD identity**: Domain 생성 시점부터 identity 소유.
- **IdGenerator abstraction**: Test 결정성 (Fake 주입) + Port/Adapter 원칙.
- **Hexagonal**: Port (application/ports.py) ↔ Adapter (infrastructure/id_generator.py).

## Reconsider When

- 성능 병목 실측 (백만 건 이상 스케일)
- Sequential public ID 명시적 요구 (인간 친화 URL)
- 다른 모듈이 identity 발급 필요 → `src/shared_kernel/` 로 이전 (약 5분)
- PG18+ 안정화 실패 or 지연 시 UUIDv4 fallback 검토

## Migration Path (미래 PG 도입 시)

Interface (`IdGenerator`) 유지, impl 만 확장:
- `UuidV7Generator` (in-memory) → `DbUuidV7Generator` (PG native) 또는 그대로 유지 (app 발급, DB 저장)
- Domain/DTO/Repository interface 변경 없음
- PG schema: `id UUID PRIMARY KEY DEFAULT uuidv7()`

Estimated churn: 스키마 정의 + connection 코드만.

## References

- [ADR 2026-07-04 id-strategy](./2026-07-04-id-strategy.md) — 이전 결정 (bigint)
- RFC 9562 (UUIDv7 표준)
- Cybertec benchmark: UUIDv4 vs bigint (참고)
- `uuid-utils` package — `compat.uuid7()` 는 stdlib `uuid.UUID` 호환
- 프로젝트 원칙: [xp.md § Simple Design](../architecture/principles/xp.md)
