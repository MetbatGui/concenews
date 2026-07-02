# DDD (Domain-Driven Design)

## 코어 원칙

### 도메인 경계

비즈니스 로직을 명확한 도메인으로 분리. 각 도메인은 독립적 책임을 가짐.

### 도메인 독립성

- 각 도메인은 독립적 저장소 유지
- 도메인 내부 구현은 외부에 노출하지 않음

### 느슨한 결합

- 도메인 간 참조는 ID만 사용
- 직접적 객체 참조 금지

### 응집도

도메인 간 관계는 Application Layer에서 조율. 도메인 자체는 순수 비즈니스 로직만 포함.

---

## 4계층 아키텍처 (Clean Architecture)

```
┌──────────────────────────────────────────────┐
│  Presentation          Infrastructure         │
│  (FastAPI router)      (SQLAlchemy impl)      │
│         │                      │              │
│         └──────────┬───────────┘              │
│                    ▼                          │
│         ┌──────────────────────┐              │
│         │   Application         │              │
│         │  (Use Case/Command)   │              │
│         │         │             │              │
│         │         ▼             │              │
│         │  ┌─────────────────┐  │              │
│         │  │     Domain      │  │              │
│         │  │  (Entity, VO,   │  │              │
│         │  │   Service)      │  │              │
│         │  └─────────────────┘  │              │
│         └──────────────────────┘              │
└──────────────────────────────────────────────┘
```

**의존성 규칙:** Domain ← Application ← (Presentation, Infrastructure)

- Domain: 외부 의존 없음 (표준 라이브러리만)
- Application: Domain만 import
- Presentation/Infrastructure: Domain, Application import 가능

---

## 디렉토리 구조 (News Context 예시)

```
modules/news/
├── domain/
│   ├── entities.py           # News (Aggregate Root)
│   ├── value_objects.py      # NewsId, Title, Source
│   ├── events.py             # NewsFetched (Domain Event)
│   ├── services.py           # Domain Service (비즈니스 규칙)
│   └── repository.py         # NewsRepository 인터페이스 (Port)
├── application/
│   ├── commands.py           # FetchNewsCommand, Handler
│   ├── queries.py            # GetNewsQuery, Handler
│   └── dtos.py               # NewsDTO
├── infrastructure/
│   ├── persistence/
│   │   └── sqlalchemy_news_repository.py   # Repository 구현
│   └── messaging/
│       └── event_bus_publisher.py          # Domain Event 발행
├── presentation/
│   └── api.py                # FastAPI 라우터
└── __init__.py
```

---

## 지켜야 할 규칙 3가지

1. **Domain은 외부 import 금지**

   ```python
   # ❌ 금지
   from sqlalchemy import Column
   from fastapi import APIRouter

   # ✅ OK
   from typing import List
   ```
2. **Application은 Domain만 import**

   ```python
   # ❌ 금지
   from news.infrastructure.persistence import SQLAlchemyNewsRepository

   # ✅ OK
   from news.domain.repository import NewsRepository
   from news.domain.entities import News
   ```
3. **Presentation이 의존성 조립 담당**

   ```python
   # presentation/api.py
   repo = SQLAlchemyNewsRepository(db_session)
   publisher = EventBusPublisher(event_bus)
   fetch_service = FetchNewsService(repo, publisher)
   ```
