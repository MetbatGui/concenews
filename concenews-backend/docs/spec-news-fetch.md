# Spec: 뉴스 조회 기능

## 사용자 스토리

개발자로서, 금리/통화 관련 주요 뉴스를 조회할 수 있어야 한다.
향후 이 뉴스 데이터를 마켓 정보와 매칭하는 기초가 됨.

---

## Acceptance Criteria

1. **GET /news** 호출 시 최근 뉴스 목록 반환 (최대 50개)
   - 응답: 200 OK
   - 정렬: published_at 최근순

2. **뉴스 필드**
   ```json
   {
     "id": "uuid",
     "title": "string",
     "description": "string",
     "link": "string",
     "source": "string",
     "published_at": "ISO8601 datetime"
   }
   ```

3. **저장된 뉴스가 없으면** 빈 배열 반환 (`[]`)

4. **응답 형식**
   ```json
   {
     "news": [
       { /* NewsItem */ },
       { /* NewsItem */ }
     ],
     "count": 2
   }
   ```

---

## Out of Scope (이 기능에선 다루지 않음)

- 실시간 뉴스 크롤링/갱신 (Spike로 검토, 별도 기능)
- 뉴스 필터링 (카테고리, 키워드)
- 페이지네이션
- 뉴스 저장소 영속성 (메모리만 사용)

---

## 기술 결정

- **데이터 소스**: TheNewsAPI Basic ($9/month, 2,500 req/day)
  - Query: `interest rate OR forex OR currency`
  - 수집 주기: 15분마다 1회 (96 req/day)
  - 참고: [spikes/news_spikes/LEARNINGS.md](../spikes/news_spikes/LEARNINGS.md)
- **저장소**: Python dict/list (메모리, 테스트용)
- **향후 마이그레이션**: PostgreSQL + Redis 캐싱

---

## 다음 단계

1. **Spike** (1-2일): 뉴스 API 선택 & 데이터 구조 학습
2. **Plan**: Endpoint/Domain/Repository 설계
3. **Implementation**: TDD로 개발
