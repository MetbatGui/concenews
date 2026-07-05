# ADR: 뉴스 도메인 ID 전략

**Status**: Accepted (2026-07-05 재확정, UUID v7 로 변경)
**Date**: 2026-07-04 (초안 bigint) / 2026-07-05 (UUID v7 재확정)
**Slice**: news-fetch

## Context

NewsItem 도메인 모델의 identity 부여 방식 결정 필요.
저장소는 초기 in-memory dict, 향후 PostgreSQL.
단일 서비스 (modular monolith).

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| UUID v4 | 분산 가능, 예측 불가 | PG B-tree page split, WAL bloat, 인덱스 밀도 79% |
| **UUID v7** | 시간순 정렬, PG 인덱스 밀도 90%, PG18+ (2025) native | 외부 dep (`uuid-utils`), 지금 필요성 borderline |
| bigint sequence | 최소 공간 (8B), 인덱스 최적 (97%), 순차 삽입 | 예측 가능, 분산 불가, ORM 시 리소스 URL 노출 문제 |

## Decision

**UUID v7** — `IdGenerator` (application port) 가 발급, 생성 시 필수.

- Domain: `id: UUID` (필수, 생성 시점에 발급됨)
- Application: `ports.py` — `IdGenerator` Protocol
- Infrastructure: `id_generator.py` — `UuidV7Generator` impl (`uuid_utils.compat.uuid7`)
- **위치**: `src/modules/news/` (news 모듈 로컬)
  - Rule of Three: 첫 impl 은 로컬. 두 번째 모듈 (market-info 등) 이 identity 발급 필요 시 `src/shared_kernel/` 로 이전.
- 미래 PG: `UUID PRIMARY KEY DEFAULT uuidv7()` (PG18+ native)
- Repository: 순수 저장 (id 부여 책임 없음)
- DTO: `id: UUID` (JSON 직렬화 시 str)

**Usage**:
```python
item = NewsItem(id=id_gen.generate(), title=..., link=..., ...)
repo.save(item)
```

## Rationale

- **시간순 정렬**: v7 앞 48비트 = timestamp. `published_at` 정렬과 자연 정합.
- **PG 인덱스 friendly**: v7 인덱스 밀도 90.09% vs v4 79.06%. 순차성 확보로 page split 완화.
- **분산 대응 여지**: 미래 마이크로서비스 분리 시 collision-free 자연.
- **Public identifier**: URL (`/news/{id}`) 노출 시 sequential 예측 불가 (bigint 대비 정보 은닉).
- **PG18+ native**: 2025 정식 지원 예정 (`uuidv7()` 함수 stdlib).
- **DDD identity**: Domain 은 생성 시점부터 identity 소유. Anemic (Optional id) 회피.
- **IdGenerator abstraction**: Test 결정성 (Fake 주입) + Port/Adapter 분리 원칙.
- **Hexagonal**: Port (application/ports.py) ↔ Adapter (infrastructure/id_generator.py) 분리.

## bigint 대비 UUID v7 선택 이유 (재고 결과)

초안은 bigint 였으나 재고 결과 UUID v7 로 전환:

- **성능 차이 무의미한 규모**: 뉴스 수백~수천 건. bigint 대비 UUID v7 오버헤드 부담 없음.
- **Public URL 노출**: `/news/1`, `/news/2` 순차 노출 = 정보 은닉 부족 (crawling, enumeration 취약).
- **미래 분산 대비**: 마이크로서비스 분리 시 bigint 는 counter 조정 필요, UUID 는 자동.
- **PG18+ native 예정**: 2025 정식 지원 안정화 확실. 조기 채택 리스크 낮음.
- **Portfolio 가치**: UUID v7 (RFC 9562) 최신 표준 채택 = 최신 관행 인지 신호.

## Reconsider When

- 성능 병목이 실제 측정됨 (백만 건 이상 스케일)
- Sequential public ID 가 명시적으로 요구됨 (예: 인간 친화 URL)
- 다른 모듈이 identity 발급 필요 → `src/shared_kernel/` 로 이전 (파일 이동 + import 갱신, 약 5분)

## Migration Path (미래 PG 도입 시)

Interface (`IdGenerator`) 유지, impl 만 확장:
- `UuidV7Generator` (in-memory) → `DbUuidV7Generator` (PG native) or 그대로 유지 (app 이 발급, DB 저장)
- Domain / DTO / Repository interface 변경 없음
- PG schema: `id UUID PRIMARY KEY DEFAULT uuidv7()` (PG18+)
Estimated churn: 스키마 정의 + connection 코드만.

## References

- RFC 9562 (UUIDv7 표준)
- Cybertec benchmark: UUIDv4 vs bigint (참고, v7 로 완화)
- `uuid-utils` package (Rust binding, `compat.uuid7()` 는 stdlib `uuid.UUID` 호환)
- 프로젝트 원칙: [xp.md § Simple Design](../architecture/principles/xp.md)

## History

- 2026-07-04: 초안, bigint sequence Accepted
- 2026-07-05: UUID v7 로 재확정. bigint 는 sequential URL 노출 & 미래 분산 대응 부족으로 폐기.
