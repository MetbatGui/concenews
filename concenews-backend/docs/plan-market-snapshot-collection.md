# Plan: 거래량 상위 거시경제 마켓 스냅샷 수집

**Spec**: [spec-market-snapshot-collection.md](./spec-market-snapshot-collection.md)
**상태**: 승인됨

## 설계 요약

기존 `market_snapshot` 테이블을 사용한다. 새 Snapshot 서비스는 Gamma에서 최근 24시간 거래량 상위 200개를 읽고, 분류 Repository에서 유효한 MACRO 식별자를 읽어 교집합 상위 50개를 저장한다.

```text
Scheduler (5분)
  -> MarketSnapshotService.run()
       -> Gamma: 활성 마켓 상위 200개 (volume24hr 내림차순)
       -> PostgreSQL: 유효한 MACRO 분류 ID
       -> 상위 50개 선정
       -> PostgreSQL: market_snapshot 행 저장
```

외부 HTTP는 `MarketSourcePort`의 확장 메서드와 Gamma 어댑터에 둔다. 선정·변환 규칙은 Domain/Application에 두며, SQLAlchemy 접근은 Snapshot Repository에 한정한다.

## Task 1 — Domain·Repository Walking Skeleton

**브랜치/PR**: `codex/market-snapshot-collection-domain-repository`
**상태**: 완료 ([PR #35](https://github.com/MetbatGui/concenews/pull/35))

- `MarketSnapshot` 불변 Domain 모델 구현
- Snapshot Repository Port와 PostgreSQL 구현·ORM 추가
- 기존 `market_snapshot` 스키마와 ORM의 계약을 Integration Test로 검증
- 실제 PostgreSQL에서 스냅샷 한 건 저장·조회 검증

**완료 기준**: 실제 DB에 수집 시각이 다른 동일 마켓 스냅샷 두 건이 보존된다.

## Task 2 — Gamma 변환·선정 서비스

**브랜치/PR**: `codex/market-snapshot-collection-service`

- Gamma 응답의 JSON 문자열 배열과 숫자 문자열 변환 구현
- 100개 단위 두 페이지로 상위 200개 조회 구현
- 분류 수집 한도를 100개에서 200개로 확대
- 유효한 MACRO 분류 후보에서 거래량 순 상위 50개를 선정하는 규칙 구현
- 유효한 MACRO 분류와 교집합한 상위 50개를 저장하는 서비스 구현
- `httpx.MockTransport` fixture 기반 Unit/Integration Test 추가

**완료 기준**: 200개 후보 fixture에서 MACRO 50개만 거래량 순서대로 저장되고, 후보가 부족하면 가능한 수만 저장된다.

## Task 3 — Scheduler 조립과 운영 계약

**브랜치/PR**: `codex/market-snapshot-collection-scheduler`

- Snapshot 서비스 Composition Root와 `market_snapshot` 작업 등록
- 기본 주기 `MARKET_SNAPSHOT_INTERVAL=300` 환경 변수 추가
- 작업별 Session·HTTP 클라이언트 종료 및 실패 격리 검증
- 기존 Scheduler 컨테이너 smoke 검증에 새 작업 등록을 반영

**완료 기준**: Fake Gamma/실제 PostgreSQL 조합에서 Scheduler 작업이 스냅샷을 저장하고 `just check-branch-green`이 통과한다.

## 테스트 전략

Classicist 원칙에 따라 서비스 내부의 Domain·Repository·실제 PostgreSQL 조합은 함께 검증한다. Gamma HTTP와 시간처럼 프로세스 밖 경계만 Fake로 대체한다. 자동 테스트는 결정적이어야 하며, 실제 Gamma 호출은 수동 검증에만 사용한다.

## Definition of Done

- [ ] Task 1~3 PR이 각각 `master`에 병합됨
- [ ] `just check-branch-green` 통과
- [ ] Scheduler 컨테이너가 5분 주기 스냅샷 작업을 등록함
- [ ] 최근 24시간 거래량 상위 200개 중 유효한 MACRO 상위 50개만 저장됨
- [ ] 실제 Gamma API로 수동 확인 후 결과를 PR에 기록함
