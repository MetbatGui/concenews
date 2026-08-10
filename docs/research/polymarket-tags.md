# Polymarket 태그 조사

## 질문

활성 Polymarket 마켓을 매크로·비매크로로 분류하기 위해 어떤 조회·태그·캐시 전략을 사용해야 하는가?

## 관찰

- Gamma API의 활성 마켓 조회는 `limit=100`, `offset`, `active=true`, `order=volume24hr`, `ascending=false` 조합을 사용한다.
- 마켓 목록에는 태그가 포함되지 않아 `/markets/{id}/tags`를 별도로 조회해야 한다.
- 다중 `tag_ids` 필터는 신뢰할 수 없어, 전체 활성 마켓을 조회한 뒤 태그 기반으로 분류한다.
- 태그 조회는 비동기 병렬화가 가능하며, 실측 50회 호출은 약 0.61초였다.
- 분류 결과는 `end_date` 기준으로 캐시할 수 있어 별도 만료 작업이 필요하지 않다.

## 결론

비매크로 블랙리스트를 먼저 적용하고, 그 다음 매크로 화이트리스트를 적용한다. 어느 쪽에도 속하지 않으면 저장하지 않는다. 태그 집합과 분류 규칙의 상세 목록은 [마켓 분류 Spec](../../concenews-backend/docs/spec-market-tracking.md)이 관리한다.

## 연결

- [Polymarket API ADR](../decisions/2026-07-12-polymarket-api-choice.md)
- [마켓 필터링 ADR](../decisions/2026-07-12-market-filtering-strategy.md)
