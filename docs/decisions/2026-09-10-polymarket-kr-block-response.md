# ADR: Polymarket 국내 접속 차단 대응 — 우회 배포 보류

**Status**: Accepted
**Date**: 2026-09-10
**Slice**: Cross-cutting

## Context

2026-08-18 방송통신심의위원회가 Polymarket 을 "도박을 방조하거나 도박장소 개설을 목적으로 하는 정보" 로 판단해 접속차단을 의결했고, 2026-08-20 부터 시행됐다. 국내 네트워크에서 직접 실측한 결과 `gamma-api.polymarket.com`·`data-api.polymarket.com` 을 포함한 전 도메인이 HTTP 451(Unavailable For Legal Reasons)을 반환한다. 응답 헤더(`Server: cloudflare`, `CF-RAY: ...-ICN`)로 보아 한국 ISP 의 SNI 차단이 아니라 **Polymarket 측 Cloudflare 설정이 한국발 요청을 지역 차단**하는 구조다.

`MarketClassifierService`·`MarketSnapshotService`·`MarketParticipantSnapshotService` 전부 이 두 API 에 의존해, 국내에서 배포하면 데이터 수집 자체가 불가능하다.

비Korea 리전(Google Colab 실측)에서는 두 API 모두 정상 응답(200 OK, 실제 JSON 데이터)한다 — 지역 차단이며, 리전 이전으로 우회 가능함이 기술적으로 확인됐다.

법적 판단은 단순하지 않다. 방미심위가 인용한 근거는 형법 246·247(도박·도박개장, 행위자를 겨냥)이 아니라 **정보통신망 심의규정상 "정보" 유통**이다. 순수 조회·분석 도구(베팅 기능 없음)는 형법 구성요건은 자연히 안 채우지만, 실시간 확률·가격 정보 자체를 가공 없이 노출하는 형태로 서비스가 확장되면 "정보 유통" 이론에 걸릴 여지가 남는다.

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| A. 해외 리전 배포 즉시 진행 | 기술적으로 이미 검증됨(Colab 200 OK). 데이터 수집 즉시 재개 | 법적 판단 없이 규제 우회를 실행하는 셈. "정보 유통" 이론 리스크를 그대로 안고 감 |
| B. 정식 법률자문 먼저 | 법적 불확실성을 가장 확실하게 해소 | 개인·비상업·무사용자 단계의 리스크 규모 대비 비용(수십~수백만 원)이 비례하지 않음 |
| C. 결정 보류, 재판단 시점을 명시 | 현재 단계 실행 리스크가 사실상 없음(로컬 개발은 이 차단과 무관). 비용 없이 리스크 회피 | 실제 배포가 필요해지는 시점에 다시 멈춰서 판단해야 함 |

## Decision

**옵션 C 채택.** 지금은 해외 리전 배포도, 정식 법률자문도 진행하지 않는다. 로컬 개발(Fake source 기반 테스트, `just check-branch-green`)은 이 차단과 무관하게 계속한다. 재판단은 아래 "Reconsider When" 조건이 발생할 때 한다.

## Rationale

한국 규제기관의 집행은 자원 배분 문제다 — 실제 개입 대상은 통상 대규모 상업적 우회 서비스나 실제 베팅 중계 운영자이고, 사용자가 없고 베팅 기능 자체가 없는 개인 비상업 프로젝트는 인지될 경로(신고·언론노출·금전거래)가 없다. 형법 246·247 의 구성요건(베팅 행위, 도박장 개설)도 순수 조회 도구엔 자연히 안 걸린다.

이 낮은 실행 리스크 대비, 정식 법률자문 비용은 비례하지 않는다. 반대로 기술적 우회(옵션 A)는 이미 검증됐으므로 "지금 당장 결정해야 서두를 이유" 도 없다 — 필요해지는 시점에 언제든 재개 가능한 옵션을 미리 소모할 이유가 없다.

## Reconsider When

- 실사용자가 유의미하게 늘어날 때
- 유료화·상업 서비스로 전환할 때
- 실시간 확률·가격을 가공 없이 그대로 화면에 노출하는 형태로 제품이 확장될 때("정보 유통" 이론에 더 가까워짐)
- 언론·SNS 노출이 발생할 때
- 민원이 접수될 때

위 조건 중 하나라도 발생하면 정식 법률자문(옵션 B)부터 다시 진행한다.

## References

- [연합뉴스: 예측시장 폴리마켓 국내 접속차단…방미심위 "사행성 인정"](https://www.yna.co.kr/view/AKR20260818123500017)
- [CoinDesk: South Korea joins more than 30 jurisdictions restricting Polymarket access](https://www.coindesk.com/business/2026/08/18/south-korea-joins-more-than-30-jurisdictions-restricting-polymarket-access)
- 2026-09-10 세션 실측: `curl` 직접 테스트(4개 도메인 전부 451, `CF-RAY: ...-ICN`), Google Colab 실측(gamma-api 200 OK, data-api 정상 스키마 응답)
- README.md § 면책
