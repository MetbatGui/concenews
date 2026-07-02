# DDD & Clean Architecture — 모듈 "안"의 구조

## 다루는 질문

> "모듈 하나의 코드를, 안에서 어떻게 나눌 것인가?"

이 문서는 **하나의 모듈 내부**만 다룬다. 모듈이 몇 개든(심지어 1개여도) 이 규칙은 그대로 적용된다. 여러 모듈이 서로 어떻게 참조하는지는 별도 문서(`modular-monolith.md`)에서 다룬다.

---

## Dependency Rule (핵심 원칙)

소스코드 의존성은 반드시 **안쪽(고수준 정책)을 향해서만** 향해야 한다. 바깥 원은 안쪽 원을 알아도 되지만, 안쪽 원은 바깥 원의 존재를 절대 몰라야 한다. (Robert C. Martin, *Clean Architecture*, 2017)

```
Presentation ──▶ Infrastructure
       │                │
       ▼                ▼
          Application
              │
              ▼
           Domain
```

## 4계층

| 계층 | 책임 | 알아도 되는 것 | 절대 몰라야 하는 것 |
|---|---|---|---|
| **Domain** | Entity/VO의 불변식, Domain Service의 도메인 규칙 | 없음 (자기 자신만) | Application, Presentation, Infrastructure 전부 |
| **Application** | Use Case 오케스트레이션 (조회 → 도메인 호출 → 저장 → 이벤트 발행) | Domain (인터페이스만) | Infrastructure 구현체, Presentation |
| **Infrastructure** | Domain이 정의한 Repository 인터페이스의 실제 구현 (DB 등) | Domain (구현 대상 인터페이스) | Application, Presentation |
| **Presentation** | 요청을 Command/Query로 조립, 의존성 조립(DI) | 전부 (조립 지점) | — |

```
modules/news/
├── domain/
│   ├── entities.py           # Aggregate Root
│   ├── value_objects.py
│   ├── events.py             # Domain Event
│   ├── services.py           # Domain Service (필요한 경우만)
│   └── repository.py         # Repository 인터페이스 (Port)
├── application/
│   ├── commands.py
│   └── queries.py
├── presentation/
│   └── api.py
└── infrastructure/
    ├── repository_impl.py
    └── orm_models.py
```

---

## Domain 계층 — DDD 전술 패턴 (Eric Evans, 2003)

### Entity / Aggregate Root

식별자로 구분되고, 자신의 불변식(invariant)을 스스로 지킨다.

```python
@dataclass
class Article:
    id: str
    title: ArticleTitle
    channel_id: ChannelId
    _events: list = field(default_factory=list)

    @classmethod
    def ingest(cls, id: str, title: str, channel_id: str) -> "Article":
        article = cls(id=id, title=ArticleTitle(title), channel_id=ChannelId(channel_id))
        article._events.append(ArticleIngested(article_id=id, channel_id=channel_id))
        return article

    def pull_events(self) -> list:
        events, self._events = self._events, []
        return events
```

### Value Object

불변, 식별자 없음. 원시 타입 집착(Primitive Obsession)을 막고 도메인 규칙을 타입 자체에 캡슐화한다.

```python
@dataclass(frozen=True)
class ArticleTitle:
    value: str
    def __post_init__(self):
        if not self.value or len(self.value) > 200:
            raise ValueError("제목은 1~200자여야 함")
```

### Domain Service

로직이 **여러 Aggregate를 넘나들어서** 어느 한쪽에 속하기 어색할 때만 만든다. 무상태(stateless), 순수 계산/규칙.

```python
class MatchingService:
    """Article과 Market, 어느 한쪽에도 속하지 않는 도메인 로직."""
    def calculate_score(self, article: ArticleSummary, market: MarketSummary) -> MatchScore:
        keyword_score = self._keyword_overlap(article.keywords, market.keywords)
        time_score = self._time_proximity(article.published_at, market.resolves_at)
        return MatchScore(keyword_score * 0.6 + time_score * 0.4)
```

> 모든 모듈에 억지로 Domain Service를 만들 필요는 없다. News/Markets처럼 단일 Aggregate로 끝나는 로직은 Application Service → Aggregate로 바로 가도 충분하다. Matching처럼 다중 Aggregate 조율이 필요한 곳에만 둔다.

### Repository (= Port)

Domain이 정의하는 계약. `domain/`은 `infrastructure/`를 절대 모른다.

```python
class ArticleRepository(ABC):
    @abstractmethod
    def save(self, article: Article) -> None: ...
    @abstractmethod
    def get(self, article_id: str) -> Article: ...
    @abstractmethod
    def next_id(self) -> str: ...
```

### Domain Event

Aggregate에서 발생하는 "사실". Domain 계층에 정의하되, 다른 모듈에 노출할 땐 최소 필드만 담는다 (상세는 `integration.md`).

---

## Application 계층 — Application Service (= Command/Query Handler)

Domain 지식을 갖지 않고 **순서만 조율**한다. Repository는 인터페이스로만 참조한다.

```python
def handle_ingest_article(command: IngestArticle, repo: ArticleRepository) -> str:
    article = Article.ingest(id=repo.next_id(), title=command.title, channel_id=command.channel_id)
    repo.save(article)
    for event in article.pull_events():
        event_bus.publish(event)
    return article.id
```

Command/Query DTO도 이 계층에 둔다. 1인 개발 규모에서는 별도 Bus 클래스를 Command/Query로 나누지 않고 `MessageBus` 하나로 통합해도 무방하다(Event는 의미론이 달라 별도 유지 — `integration.md` 참고).

---

## Infrastructure 계층

Domain이 정의한 인터페이스의 구현체만 놓는다.

```python
class SqlAlchemyArticleRepository(ArticleRepository):
    def save(self, article: Article) -> None: ...
    def next_id(self) -> str: ...
```

## Presentation 계층 — 유일한 조립 지점

```python
@router.post("/articles")
def create_article(payload: dict, session=Depends(get_session)):
    repo = SqlAlchemyArticleRepository(session)   # Infrastructure를 여기서 주입
    return handle_ingest_article(IngestArticle(**payload), repo)
```

---

## 이 문서가 지켜주는 것

- Infrastructure(DB, 프레임워크)를 갈아끼워도 Domain/Application 코드는 안 바뀜
- Repository를 Fake로 교체해 Domain/Application을 DB 없이 테스트 가능
- 도메인 규칙(불변식, 계산 로직)이 Aggregate·Domain Service에 응집되어 Application에 흩어지지 않음

## 1인 개발 간소화 지점 (오버엔지니어링 방지)

| 유지할 것 (DDD 본질) | 생략 가능한 것 (배관/의전) |
|---|---|
| Entity, Value Object, Aggregate 불변식 | Command Bus / Query Bus 완전 분리 → `MessageBus` 통합 |
| Repository 인터페이스(ABC) + 구현 분리 | Input/Output Boundary, Presenter 별도 클래스 |
| Domain Service (다중 Aggregate 조율 시만) | `v1/`, `fastapi/`, `rest/` 식 4단 중첩 경로 |
| Domain Event | Domain Event ↔ Integration Event 완전 분리 (`integration.md`에서 절충안 제시) |
