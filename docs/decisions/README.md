# ADR Index

> 아키텍처 결정 로그 (Architecture Decision Records)
> 프로세스: [../adr-process.md](../adr-process.md)

---

## 카테고리

### Identity & Storage

| Date | ADR | Status |
|------|-----|--------|
| 2026-07-04 | [id-strategy (bigint)](./2026-07-04-id-strategy.md) | Superseded by 2026-07-05 |
| 2026-07-05 | [id-strategy UUID v7](./2026-07-05-id-strategy-uuidv7.md) | Accepted |

### Process & Convention

| Date | ADR | Status |
|------|-----|--------|
| 2026-07-05 | [test-isolation-cache-clear](./2026-07-05-test-isolation-cache-clear.md) | Accepted |

### Module Boundaries

_(없음, 필요 시 추가)_

### External Dependencies

_(없음, 필요 시 추가)_

---

## Status 라이프사이클

```
Proposed → Accepted → Superseded by ... | Deprecated
```

- **Proposed**: 초안, 논의 중
- **Accepted**: 채택, 코드/문서 반영됨
- **Superseded by X**: 다른 ADR 이 폐기. 원문 보존, 새 ADR 로 이동.
- **Deprecated**: 폐기, 대체 없음 (드묾)

---

## 신규 ADR 작성 순서

1. Trigger 매칭 확인 ([adr-process.md](../adr-process.md))
2. `YYYY-MM-DD-{slug}.md` 파일 생성
3. 이 파일 (README.md) 카테고리에 추가
4. 관련 docs (spec/plan/CLAUDE/convention) 갱신 + ADR 링크 명시
5. Superseded 인 경우: 원 ADR Status 갱신
