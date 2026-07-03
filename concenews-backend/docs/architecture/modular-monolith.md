# Modular Monolith — 모듈 "간"의 경계

## 다루는 질문

> "News, Markets, Matching처럼 서로 다른 바운디드 컨텍스트가 한 프로세스 안에 있을 때, 서로 어떻게 접근할 것인가?"

이 문서는 **모듈 내부를 어떻게 나누는지(`ddd.md` 참고)와는 무관하게**, 모듈이 2개 이상일 때 항상 필요한 규칙을 다룬다. 계층이 몇 개든 상관없다.

---

## 핵심 원칙 — 결합의 종류를 통제한다

같은 프로세스 안에 있는 한, 모듈 간 **완전한 무결합(zero coupling)은 물리적으로 불가능**하다. 대신 "어떤 종류의 결합만 허용할지"를 통제한다.

| 결합 종류 | 예시 | 허용 여부 |
|---|---|---|
| **구현 결합** (Implementation Coupling) | Matching이 News의 `Article` 엔티티, `NewsService` 클래스를 직접 import | ❌ 금지 |
| **계약 결합** (Contract Coupling) | Matching이 News가 노출한 `GetArticleSummary` DTO만 import | ✅ 허용 |

비유: 손님이 주방에 들어가 요리사에게 직접 지시하는 것(구현 결합) vs 손님이 메뉴판을 보고 주문만 하는 것(계약 결합). 메뉴판을 안다는 것 자체는 결합이지만, **모듈 경계가 허용하는 유일하고 통제된 결합**이다.

---

## 구조 — `public.py` + 버스

```
modules/
├── news/
│   ├── domain/ ...            (ddd.md 참고)
│   ├── application/ ...
│   ├── presentation/ ...
│   ├── infrastructure/ ...
│   ├── public.py               ★ 이 모듈이 외부에 노출하는 유일한 창구
│   └── bootstrap.py
├── markets/
│   └── public.py
└── matching/
    └── public.py

shared_kernel/
├── message_bus.py              # Command/Query 공용, 1:1 응답 필요
└── event_bus.py                # Event 전용, 0:N 구독, fire-and-forget
```

```python
# modules/news/public.py — 공개 계약
from application.queries import GetArticleSummary, handle_get_article_summary
from application.commands import IngestArticle, handle_ingest_article
from domain.events import ArticleIngested

__all__ = ["GetArticleSummary", "IngestArticle", "ArticleIngested"]
```

```python
# modules/matching/application/use_cases.py
from modules.news.public import GetArticleSummary        # ✅ 허용 — 계약만 앎
from modules.news.domain.entities import Article          # ❌ import-linter가 차단

def handle_find_matches(command):
    article = message_bus.dispatch(GetArticleSummary(article_id=command.article_id))
    ...
```

---

## Command/Query Bus vs Event Bus

크로스 모듈 통신은 두 종류로 나뉘고, 의미론이 다르므로 클래스도 분리 유지한다.

| | Command / Query (MessageBus) | Event (EventBus) |
|---|---|---|
| 의미 | "데이터를 달라" / "이 작업을 해줘" | "이런 일이 일어났다" |
| 응답 | 있음, 발행자가 기다림 | 없음, 발행자는 신경 안 씀 |
| 핸들러 수 | 정확히 1개 | 0~N개 (여러 구독자) |
| 결합 방향 | 호출자가 대상 모듈을 앎 | 발행자는 구독자를 전혀 모름 |

```python
class MessageBus:
    """Command/Query 공용. 1:1, 반환값 있음."""
    def register(self, message_type, handler):
        if message_type in self._handlers:
            raise ValueError(f"{message_type.__name__} 이미 등록됨")
        self._handlers[message_type] = handler

    def dispatch(self, message):
        return self._handlers[type(message)](message)


class EventBus:
    """0:N, fire-and-forget."""
    def subscribe(self, event_type, handler):
        self._handlers[event_type].append(handler)

    def publish(self, event):
        for handler in self._handlers[type(event)]:
            handler(event)
```

> Command와 Query를 굳이 별도 클래스로 나눌 필요는 없다(둘 다 1:1, 응답 있음). 하지만 Event는 0:N에 응답이 없다는 점에서 의미론이 완전히 달라 별도 클래스를 유지한다.

---

## import-linter로 강제

```toml
[[tool.importlinter.contracts]]
name = "Matching은 News의 public.py를 통해서만 접근"
type = "forbidden"
source_modules = ["modules.matching"]
forbidden_modules = [
    "modules.news.domain",
    "modules.news.application",
    "modules.news.infrastructure",
    "modules.news.presentation",
]
# modules.news.public 은 목록에 없으므로 허용됨
```

이 계약은 각 모듈 쌍마다 반복 작성해야 한다. 한 모듈에만 걸면 그 모듈은 안전해도, 다른 모듈이 그 모듈의 내부를 참조하는 걸 막을 수 없다.

---

## 유일한 결합 지점 — `main.py`

두 모듈이 서로 몰라도, 어딘가는 모든 모듈을 조립해야 한다. 이 결합은 피할 수 없는 필요악이므로 위치를 한 곳에 고정한다.

```python
# main.py — 유일하게 모든 모듈을 알아도 되는 곳
from modules.news.bootstrap import register as register_news
from modules.markets.bootstrap import register as register_markets
from modules.matching.bootstrap import register as register_matching

register_news()
register_markets()
register_matching()
```

---

## 계층 구조 (Module Internal)

각 모듈 내부는 4계층으로 나뉨:

| 계층 | 역할 | 예시 |
|---|---|---|
| **Domain** | 비즈니스 규칙, 엔티티, 도메인 로직 | `NewsItem` 엔티티, `published_at` 검증 규칙 |
| **Application** | Use Cases, Commands, Queries, 비즈니스 오케스트레이션 | `GetNewsCommand`, `FetchNewsUseCase` (아직 미구현) |
| **Presentation** | HTTP/API 응답 계약, DTO | `GetNewsResponse`, `NewsItemResponse` (schemas.py) |
| **Infrastructure** | 데이터 접근, 외부 서비스 호출 | `NewsRepository`, API 클라이언트 |

**규칙**:
- Domain/Application → 외부 의존성 없음 (순수 비즈니스 로직)
- Presentation → HTTP 응답만 정의 (비즈니스 로직 없음)
- Infrastructure → DB, 외부 API만 (도메인 규칙 없음)

**예시: News 모듈**:
```
src/modules/news/
├── domain/
│   └── (NewsItem 엔티티, 검증 규칙 — 아직 미구현)
├── application/
│   └── (Commands, Queries — 아직 미구현)
├── presentation/
│   └── schemas.py  ← GetNewsResponse DTO ✅
├── infrastructure/
│   └── (NewsRepository, TheNewsAPI 클라이언트 — 아직 미구현)
├── public.py  ← 외부는 여기서만 import
└── bootstrap.py
```

---

## 이 문서가 지켜주는 것

- 한 모듈의 내부 리팩터링이 다른 모듈에 전파되지 않음
- 모듈 하나를 나중에 별도 서비스(MSA)로 뽑아낼 때 전환 비용이 작음 (`integration.md` 참고)
- "Matching = Core Domain, News/Markets = Supporting Domain"처럼 모듈 간 우선순위·의존 방향을 코드로 강제 가능

## 1인 개발 간소화 지점

| 유지할 것 | 생략 가능한 것 |
|---|---|
| `public.py`를 통한 접근만 허용 (import-linter) | Port In/Out을 별도 인터페이스 클래스로 이중 정의 |
| Command/Query vs Event 구분 | Command/Query를 별도 Bus 클래스로 분리 (MessageBus로 통합 가능) |
| 모듈 간 독립성 규칙 (`forbidden` 계약) | — (이건 모듈러 모놀리스의 핵심이라 생략 불가) |
