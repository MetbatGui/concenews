# Docstring Convention

> Google Style Docstring + Clean Code
> 코드 중간 주석 NO, docstring으로만

---

## Google Style Format

### 함수

```python
def fetch_news_from_api(api_key: str, limit: int = 50) -> List[NewsItem]:
    """NewsAPI에서 뉴스를 조회하고 NewsItem으로 변환.

    Args:
        api_key: NewsAPI 인증 키.
        limit: 조회할 뉴스 개수 (기본 50).

    Returns:
        뉴스 아이템 리스트.

    Raises:
        NewsAPIError: API 호출 또는 응답 파싱 실패.
    """
```

### 클래스

```python
class NewsRepository:
    """메모리 기반 뉴스 저장소.

    임시 저장용. 향후 PostgreSQL로 마이그레이션 예정.
    """

    def store(self, item: NewsItem) -> None:
        """뉴스 아이템 저장.

        Args:
            item: 저장할 뉴스 아이템.
        """
```

### Domain Model (Pydantic)

```python
class NewsItem(BaseModel):
    """뉴스 아이템 도메인 모델.

    Attributes:
        id: 고유 식별자 (URL 해시).
        title: 뉴스 제목.
        description: 요약 설명.
        link: 기사 링크.
        source: 뉴스 출처 (신문사명).
        published_at: 발행 시간 (ISO8601).
    """

    id: str
    title: str
    description: Optional[str] = None
    link: str
    source: str
    published_at: datetime
```

### 테스트 함수 (GWT 패턴)

```python
def test_get_news_returns_200(self, client):
    """GET /news 엔드포인트는 200 OK를 반환한다.

    Given: FastAPI test client
    When: GET /news 호출
    Then: 응답 상태 코드는 200
    """
    response = client.get("/news")
    assert response.status_code == 200
```

---

## 규칙

### DO ✅

```python
# 함수 목적 명확
def parse_newsapi_response(raw: dict) -> List[NewsItem]:
    """뉴스 API 응답을 도메인 모델로 변환."""
    return [NewsItem(**article) for article in raw["articles"]]

# 메서드 책임 분명
def validate_and_save(self, item: NewsItem) -> bool:
    """아이템 검증 후 저장. 검증 실패시 False 반환."""
    if not item.title:
        return False
    self.store(item)
    return True
```

### DON'T ❌

```python
# 나쁨: 코드 중간 주석
def process_news(data):
    # API에서 받은 데이터를 순회
    items = []
    for article in data["articles"]:  # 각 기사 처리
        # URL을 해시로 변환
        id_hash = hashlib.sha256(article["url"].encode()).hexdigest()
        # NewsItem 생성
        item = NewsItem(id=id_hash, ...)
        items.append(item)
    return items
```

### 대신 ✅

```python
# 좋음: docstring + 명확한 네이밍
def convert_articles_to_items(articles: List[dict]) -> List[NewsItem]:
    """API 응답의 기사 목록을 도메인 모델로 변환.

    각 기사의 URL을 고유 ID로 사용.

    Args:
        articles: 원본 기사 딕셔너리 리스트.

    Returns:
        NewsItem 리스트.
    """
    items = []
    for article in articles:
        item = NewsItem(
            id=_hash_url(article["url"]),
            title=article["title"],
            description=article.get("description"),
            link=article["url"],
            source=article["source"]["name"],
            published_at=parse_iso8601(article["publishedAt"]),
        )
        items.append(item)
    return items


def _hash_url(url: str) -> str:
    """URL을 SHA256 해시로 변환."""
    return hashlib.sha256(url.encode()).hexdigest()
```

---

## 주석 사용 기준

### 주석 필요 ✅
- **WHY**: 비직관적인 비즈니스 로직
  ```python
  # NewsAPI는 최대 100 req/day이므로 24시간 기준 throttle
  if request_count > DAILY_LIMIT:
      raise RateLimitError()
  ```

- **제약사항**: 숨은 한계
  ```python
  # O(n²) 스캔. 데이터 <1000개일 때만 사용.
  def find_duplicates(items: List[str]) -> List[str]:
  ```

### 주석 불필요 ❌
- 명백한 코드
  ```python
  # 안 좋음: 뻔함
  user_name = user.name  # 유저 이름 설정
  
  # 좋음: 주석 없음
  user_name = user.name
  ```

- 네이밍이 명확한 경우
  ```python
  # 안 좋음: 설명 주석
  items = [x for x in articles if x["published_at"] > cutoff]
  
  # 좋음: 명확한 변수명
  recent_articles = [
      article for article in articles
      if article["published_at"] > cutoff_date
  ]
  ```

---

## Summary

| 항목 | 규칙 |
|------|------|
| **Docstring** | Google Style (모든 함수/클래스) |
| **코드 중간 주석** | 최소 (WHY & 제약만) |
| **네이밍** | 명확하게 (주석 불필요할 정도) |
| **복잡 로직** | docstring 설명 + 단위 테스트 |
