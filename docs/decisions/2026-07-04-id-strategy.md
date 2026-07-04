# ADR: 뉴스 도메인 ID 전략

**Status**: Accepted
**Date**: 2026-07-04
**Slice**: news-fetch

## Context

NewsItem 도메인 모델의 identity 부여 방식 결정 필요.
저장소는 초기 in-memory dict, 향후 PostgreSQL.
단일 서비스 (modular monolith).

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| UUID v4 | 분산 가능, 예측 불가 | PG B-tree page split, WAL bloat, 인덱스 밀도 79% |
| UUID v7 | 시간순 정렬, PG18+ (2025) native | 외부 dep (`uuid-utils`), 단일 서비스에서 과잉 |
| bigint sequence | 최소 공간 (8B), 인덱스 최적, 순차 삽입 | 예측 가능, 분산 불가 |

## Decision

**bigint sequence** — `IdGenerator` (infrastructure port) 가 발급, 생성 시 필수.

- Domain: `id: int` (필수, 생성 시점에 발급됨)
- Infrastructure: `IdGenerator` Protocol + `SequenceIdGenerator` impl (in-memory counter)
- 미래 PG: BIGSERIAL 로 impl 교체
- Repository: 순수 저장 (id 부여 책임 없음)
- DTO: `id: int`

**Usage**:
```python
item = NewsItem(id=id_gen.generate(), title=..., link=..., ...)
repo.store(item)
```

## Rationale

- **단일 서비스 monolith** → 분산 ID 불필요
- **성능**: bigint 인덱스 = 최적. Cybertec 실측 UUIDv4 vs bigint 조회 시 I/O 31,229% 증가.
- **공간**: bigint 8B vs UUID 16B. 대규모 테이블에서 백업/복원 시간 차이.
- **인덱스 밀도**: integer 97.64% vs UUIDv4 79.06% vs UUIDv7 90.09%.
- **IdGenerator abstraction 정당화**: speculative 아님. Test 결정성 (Fake 주입) + Repository 순수성 (저장만) = 지금 즉시 이득. RepositoryFactory 같은 "미래 DB 종류" 투기와 구분됨.
- **DDD identity**: Domain 은 생성 시점부터 identity 소유. Anemic (Optional id) 회피.
- **리소스 노출**: `/news/{id}` 순차 노출 위험 낮음 (뉴스는 공개 데이터).
- **보안 misinterpretation**: RFC 4122 명시 — UUID 는 추측 방지용 보안 수단 아님.

## Reconsider When

- 여러 writer / 마이크로서비스 분리
- Public identifier 예측 불가능성 요구 (privacy)
- PG18+ 안정화 + 실제 분산 요구

## Migration Path (미래)

Interface (`IdGenerator`) 는 유지, impl 만 교체.
- `SequenceIdGenerator` → `UUIDv7Generator`
- Domain `id: int` → `id: UUID` (타입만 변경, 소유권 유지)
- DTO `id: int` → `id: str` (UUID 문자열)
- PG schema: `BIGSERIAL PRIMARY KEY` → `UUID PRIMARY KEY DEFAULT uuidv7()`
- Repository: 변경 없음 (id 부여 책임 없음)
Estimated churn: 1-2 시간 (interface 유지 덕분에 최소화).

## References

- Cybertec benchmark: UUIDv4 vs bigint (8.5M 추가 페이지 접근)
- RFC 9562 (UUIDv7 표준)
- RFC 4122 (UUID 일반, 보안 주의사항)
- 프로젝트 원칙: [xp.md § Simple Design](../architecture/principles/xp.md)
