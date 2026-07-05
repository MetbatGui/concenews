# ADR 프로세스

> 설계 결정을 immutable ADR 로 기록. 설계 문서는 최신 상태 유지.
> Michael Nygard 원안 + Fowler docs-SSOT 혼합.

---

## 원칙

- **ADR = 결정 로그** (immutable, append-only history)
- **Docs = 최신 상태 SSOT** (spec/plan/CLAUDE.md/convention 등)
- **순서**: 결정 필요 → ADR 작성 → 관련 docs 갱신 → 코드 변경

---

## 언제 ADR 을 쓰나 (trigger)

| Trigger | 예 |
|---------|-----|
| Domain 계약 변경 | id 타입, 필드 추가/삭제, invariant 변경 |
| 모듈 경계 변경 | 새 모듈, 계층 이동 (port infra → app) |
| 저장소 전략 | in-memory → PG, 스키마 |
| 외부 dependency 도입/제거 | uuid-utils, sqlalchemy |
| 아키텍처 원칙 변경 | XP/DDD/Hexagonal 규칙 |
| 프로세스 규칙 | TDD 강제, PR 단위, review-standard, ADR-first |

**Not ADR 대상** (커밋 메시지 & docs 갱신으로 충분):
- 코드 세부 (variable naming, refactor)
- Bug fix
- Nit 처리
- Test 세부 (하드코드 값 등)

---

## 파일 규칙

**위치**: `docs/decisions/YYYY-MM-DD-{slug}.md`

**slug 규칙**: kebab-case, slice 또는 topic 명 포함
- `2026-07-04-id-strategy.md`
- `2026-07-05-id-strategy-uuidv7.md`
- `2026-07-05-adr-first-process.md`

**Index**: `docs/decisions/README.md` — 모든 ADR 목록 + Status + 카테고리

---

## ADR 형식

```markdown
# ADR: {제목}

**Status**: Proposed | Accepted | Superseded by ADR-{link} | Deprecated
**Date**: YYYY-MM-DD
**Slice**: {slice-name} or Cross-cutting

## Context
문제/상황

## Options Considered
| 옵션 | Pros | Cons |

## Decision
채택안 + 세부

## Rationale
왜

## Reconsider When
언제 뒤집을지

## Migration Path (선택)
현재 → 미래 전환 방법

## References
관련 링크 (RFC, benchmark, 다른 ADR 등)
```

**금지**: `## History` 섹션 (immutable 원칙 위반).

---

## Superseded 처리 (immutable 원칙)

**결정이 뒤집힐 때**:
1. 원 ADR 은 **내용 변경 금지**. `Status: Superseded by [{new-ADR-slug}](./{new}.md)` 만 갱신.
2. 신규 ADR 파일 생성 (`YYYY-MM-DD-{topic}-v2.md` 등).
3. 신규 ADR `Context` 에 이전 ADR 링크 + 폐기 이유.

**금지**: 기존 ADR 을 갱신하며 History 섹션에 이력 누적. 이력은 파일 자체가 담당.

---

## Docs 갱신 규칙

**설계 결정 반영 섹션**: 해당 ADR 링크 명시.

예 (`plan-news-fetch.md`):
```markdown
**ID 전략**: UUID v7 — 상세는 [ADR 2026-07-05](../../docs/decisions/2026-07-05-id-strategy-uuidv7.md).
```

**이유**: docs 만 봐도 되게 하되, "왜" 답이 필요할 때 ADR 로 이동 가능.

---

## PR 체크리스트 (설계 변경 포함 PR)

- [ ] 설계 결정 trigger 매칭? → ADR 작성/갱신됨?
- [ ] Docs (spec/plan/CLAUDE/convention) 최신 상태로 갱신됨?
- [ ] Docs 에서 관련 ADR 링크 명시됨?
- [ ] Superseded 인 경우 원 ADR Status 갱신 + 신규 파일?

---

## 소급 적용 (기존 ADR)

원칙 도입 이전 결정도 필요시 소급 ADR 작성.
- 요약 파일 하나: `docs/decisions/{date}-retrospective-decisions.md`
- 또는 개별 파일: 결정마다 ADR

**판단 기준**: 미래 세션이 "왜 이 선택?" 물었을 때 답 있으면 skip, 없으면 소급 작성.
