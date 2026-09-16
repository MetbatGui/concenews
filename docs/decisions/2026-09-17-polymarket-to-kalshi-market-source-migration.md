# ADR: Market 데이터 소스 Polymarket → Kalshi 교체

**Status**: Accepted
**Date**: 2026-09-17
**Slice**: Cross-cutting (market 모듈)

## Context

[2026-09-10 ADR](./2026-09-10-polymarket-kr-block-response.md)에서 Polymarket 국내 접속 차단에 대한 대응을 "재판단 시점까지 보류"로 결정했다. 하지만 이 차단은 법적 판단과 무관하게 **기술적으로 로컬 개발 자체를 막는다** — 국내 네트워크에서 `gamma-api.polymarket.com`·`data-api.polymarket.com` 전부 HTTP 451을 반환하므로, 리전 우회 없이는 `MarketClassifierService`·`MarketSnapshotService`·`MarketParticipantSnapshotService` 개발을 로컬에서 이어갈 수 없다. 리전 우회는 2026-09-10 ADR에서 이미 보류하기로 했으므로, 이 상태로는 market 모듈 개발이 사실상 정지된다.

대안으로 조사한 Kalshi(CFTC 규제 하 Designated Contract Market, 2020년 11월부터)는:
- 한국은 Kalshi 자체의 54개국 "restricted" 목록에 별도로 올라 있으나, 이는 KYC·거래 자격 제한이며 KCSC 같은 국가 차단이 아니다.
- 공개 시세 조회 API(`/markets`, `/events`, `/markets/trades`)는 한국에서 지오블록 없이 200 OK로 정상 응답함을 직접 실측 확인했다.
- 거시경제·지정학 커버리지가 Polymarket보다 깊고, 한국 관련 시리즈(`KXCBDECISIONKOREA`, `KXSKEXPYOY` 등)도 존재한다.

기존 아키텍처는 이미 헥사고날 구조로 `MarketSourcePort`·`ParticipantSourcePort`(`application/ports.py`)를 통해 거래소를 추상화해뒀고, Polymarket 관련 구현은 `infrastructure/` 계층의 `PolymarketGammaClient`·`PolymarketDataClient` 등 어댑터로 격리돼 있다.

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| A. Polymarket 어댑터 유지, 재판단 시점까지 개발 정지 | 코드 변경 없음 | 재판단 시점이 불특정(2026-09-10 ADR의 Reconsider When 조건 발생 시) — 그동안 market 모듈 개발이 완전히 멈춤 |
| B. Polymarket 관련 코드 전부 이력에서 삭제 | 저장소가 깔끔함 | 향후 Polymarket 재판단 시 참고할 구현이 사라짐. git history 로 되돌릴 수 있다지만 삭제 자체가 "다시 안 씀"이라는 과신호 |
| C. Domain/Port 계층 유지, Polymarket 전용 Infrastructure 어댑터만 작업 트리에서 제거(git 이력엔 보존), Kalshi 어댑터 신규 구현 | Port 가 이미 거래소 비종속적으로 설계돼 재사용 가능. 이력 보존으로 향후 Polymarket 복귀도 가능. 개발 즉시 재개 가능 | Kalshi 는 서버 사이드 정렬 파라미터가 없어(`/markets`·`/events` 모두 volume/popularity sort 미지원, 공식 문서로 확인) "주요 마켓" 선정 로직을 클라이언트 사이드로 새로 설계해야 함 |

## Decision

**옵션 C 채택.**

- `application/ports.py`의 `MarketSourcePort`·`ParticipantSourcePort`·`SnapshotRepositoryPort` 등은 변경하지 않는다 — 이미 거래소 비종속적 계약이다.
- `infrastructure/`의 Polymarket 전용 어댑터(`PolymarketGammaClient`, `PolymarketDataClient` 등)는 작업 트리에서 제거한다. git history 에는 그대로 남아 필요 시 복원 가능하다.
- `KalshiMarketClient`(가칭)를 신규 구현해 동일 Port 를 구현한다.
- Polymarket 의 tag 기반 분류(`MarketClassifierService`, rate-limit 대응 배치 로직 포함)는 Kalshi 의 네이티브 `category`/`series_ticker` 필드로 대체 가능한지 재검토한다 — Kalshi 가 서버에서 이미 카테고리를 제공하면 커스텀 태그 분류 서비스 자체가 불필요해질 수 있다.
- Kalshi 는 서버 사이드 volume/popularity 정렬을 제공하지 않으므로, "주요 마켓" 선정은 `/markets/trades` 등을 이용한 클라이언트 사이드 집계로 별도 Spike·Spec 을 거쳐 설계한다 (이 ADR 범위 밖, 후속 작업).

## Rationale

Port/Adapter 경계가 이미 존재하므로 교체 비용은 어댑터 계층에 국한된다 — Domain 모델(마켓 참여자, 관측 제외 등)은 거래소 개념에 의존하지 않게 설계돼 있어 재작성이 필요 없다. 코드를 완전히 삭제하지 않고 이력으로만 보존하는 이유는, 2026-09-10 ADR 의 Reconsider When 조건(실사용자 증가, 상업화 등)이 발생해 Polymarket 접속이 다시 가능해지거나 리전 우회가 재검토될 경우 재구현 비용을 되풀이하지 않기 위함이다.

## Reconsider When

- [2026-09-10 ADR](./2026-09-10-polymarket-kr-block-response.md)의 Reconsider When 조건이 발생해 Polymarket 리전 우회/법률자문이 실제로 진행될 때 — 이 경우 두 데이터 소스를 동시에 지원할지, Polymarket 으로 되돌아갈지 다시 판단한다.
- Kalshi 가 자체 restricted 목록에서 한국을 조정하거나, 반대로 공개 조회 API 마저 지오블록할 때.

## Migration Path

1. Kalshi API 계약(인증, rate limit, 마켓/카테고리 스키마) Spike → `docs/research/kalshi-api-contract.md` 기록.
2. `MarketSourcePort`·`ParticipantSourcePort` 구현체로 `KalshiMarketClient` 신규 작성 (Walking Skeleton부터).
3. Polymarket 전용 infrastructure 파일 `git rm` (이력 보존, 작업 트리에서만 제거).
4. `MarketClassifierService`의 태그 분류 로직을 Kalshi `category` 필드 기반으로 재설계하거나, 서버 제공 카테고리로 대체해 서비스 자체를 단순화.
5. "주요 마켓" 클라이언트 사이드 집계 방식은 별도 Spec/Plan 대상 (Kalshi 서버 사이드 정렬 부재 때문).

## References

- [2026-09-10 ADR: Polymarket 국내 접속 차단 대응](./2026-09-10-polymarket-kr-block-response.md)
- [2026-07-12 ADR: Polymarket API 선택 (Gamma + CLOB)](./2026-07-12-polymarket-api-choice.md) — 데이터 소스로 Polymarket 을 처음 채택한 배경(이미 다른 ADR로 Superseded, 참고용)
- 2026-09-17 세션 실측: Kalshi `/markets`, `/events`, `/markets/trades` 한국 IP 200 OK 직접 확인; 공식 문서로 `order_by=volume` 등 정렬 파라미터 부재 확인
- Kalshi 공식: CFTC DCM 등록(2020-11), 한국 포함 54개국 restricted 목록(KYC 자격 제한, 지역 차단 아님)
