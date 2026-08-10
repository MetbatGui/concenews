# TheNewsAPI 계약 조사

## 질문

뉴스 수집 Adapter와 테스트 fixture가 공유해야 할 TheNewsAPI 응답 계약은 무엇인가?

## 확인 결과

- 응답 목록 키는 `articles`가 아니라 `data`다.
- 기사는 `title`, `description`, `url`, `source`, `published_at` 정보를 제공한다.
- `source`는 문자열로 처리할 수 있어야 한다.
- `description`은 없을 수 있다.
- 외부 API의 식별자는 도메인 식별자로 재사용하지 않고, 원본 URL을 중복 제거 기준으로 사용한다.

## 적용

- HTTP Fake 응답은 `concenews-backend/tests/fixtures/thenewsapi.py`를 단일 진실원천으로 사용한다.
- Fixture 계약 변경은 이 문서와 실제 API 수동 E2E 확인을 함께 갱신한다.
- 실제 외부 API와 PostgreSQL을 함께 쓰는 검증만 `@pytest.mark.e2e`다.

## 연결

- [Classicist 테스트 전략 ADR](../decisions/2026-08-09-classicist-test-strategy.md)
- [뉴스 조회 Spec](../../concenews-backend/docs/spec-news-fetch.md)
