# Integration — DDD/Clean Architecture × Modular Monolith

## 이 문서의 목적

`ddd.md`(모듈 안의 계층 구조)와 `modular-monolith.md`(모듈 간의 경계)는 서로 다른 질문에 답한다. 이 문서는 그 둘이 왜 별개인지 다시 짚고, 실제 코드베이스에서 어떻게 겹쳐 적용되는지, 그리고 MSA 전환 시 무엇이 남고 무엇이 사라지는지를 정리한다.

---

## 왜 별개의 문제인가

- `ddd.md`의 4계층은 **모듈이 하나뿐이어도** 필요하다 — "이 코드 안에서 도메인과 인프라를 어떻게 분리하나"
- `modular-monolith.md`의 `public.py`/버스는 **계층 구조와 무관하게** 필요하다 — "여러 도메인이 한 프로세스에 있을 때 서로 어떻게 참조하나"
- 실제로 둘 중 하나만 있는 프로젝트도 가능하다: 계층 없이 모듈만 나눈 프로젝트, 또는 모듈 하나에 계층만 4단으로 나눈 프로젝트

Clean Architecture 원전(Robert C. Martin)은 "하나의 애플리케이션" 내부 구조만 다루며, 여러 바운디드 컨텍스트가 한 프로세스에 공존하는 문제는 다루지 않는다. 이 조합은 원전에 명시되어 있지 않고, 모듈러 모놀리스 구현체들이 실무에서 두 원칙을 겹쳐 쓰는 패턴이다(예: Kamil Grzybek, *Modular Monolith with DDD*).

---

## 합쳐진 그림

```
                    [modular-monolith.md — 모듈 간 경계]
    ┌──────────────┬──────────────┬──────────────┐
    │    news/     │   markets/   │  matching/   │
    │  ┌────────┐  │  ┌────────┐  │  ┌────────┐  │
    │  │present.│  │  │present.│  │  │present.│  │  ┐
    │  │infra   │  │  │infra   │  │  │infra   │  │  │ [ddd.md —
    │  │applica.│  │  │applica.│  │  │applica.│  │  │  모듈 내부 계층]
    │  │domain  │  │  │domain  │  │  │domain  │  │  ┘
    │  └────────┘  │  └────────┘  │  └────────┘  │
    │  public.py   │  public.py   │  public.py   │  ← 유일한 접점
    └──────┬───────┴──────┬───────┴──────┬───────┘
           │              │              │
           └──────────────┴──────────────┘
              (public.py끼리, 버스 경유로만 참조)
```

## 규칙 요약 (모든 모듈에 반복 적용)

| 문서 | 방향 | 규칙 | 강제 수단 |
|---|---|---|---|
| `ddd.md` | 수직 | `domain` ← `application` ← `presentation`/`infrastructure` | import-linter `layers` 계약 |
| `modular-monolith.md` | 수평 | 모듈 간 참조는 `public.py`(계약)만 통과 | import-linter `forbidden` 계약 |

각 모듈(news, markets, matching)마다 두 계약을 **각각** 걸어야 한다. 한쪽만 걸면 다른 축의 결합이 새어나간다.

---

## 결합이 완전히 사라지지 않는 이유

쿼리버스를 쓰더라도 `GetArticleSummary` 같은 **계약(DTO) import는 여전히 필요**하다. 완전 무결합은 같은 프로세스 안에서는 불가능하며, 그게 필요하면 물리적으로 프로세스를 분리(MSA)해야 한다.

모듈러 모놀리스가 실제로 통제하는 것은 "결합을 0으로 만드는 것"이 아니라, **"구현 결합은 막고, 계약 결합만 허용하는 것"**이다.

---

## Domain Service vs Application Service — 헷갈리기 쉬운 경계

| | Domain Service (`ddd.md`) | Application Service (`ddd.md`의 Command/Query Handler) |
|---|---|---|
| 위치 | `domain/` | `application/` |
| 역할 | 여러 Aggregate를 넘나드는 도메인 규칙 | 유스케이스 오케스트레이션 (조회 → 저장 → 발행) |
| 다른 모듈 접근 | 하지 않음 | 필요시 `modular-monolith.md`의 버스를 통해 접근 |

Application Service(Handler)가 다른 모듈의 데이터가 필요하면 `MessageBus.dispatch()`를, 다른 모듈에 통지만 하면 `EventBus.publish()`를 쓴다 — 이 지점이 두 문서가 코드 레벨에서 만나는 곳이다.

```python
# modules/matching/application/use_cases.py
from modules.news.public import GetArticleSummary       # modular-monolith.md 규칙
from domain.services import MatchingService              # ddd.md 규칙

def handle_find_matches(command):
    article = message_bus.dispatch(GetArticleSummary(article_id=command.article_id))  # 모듈 간
    markets = message_bus.dispatch(GetActiveMarkets())
    matches = MatchingService().find_best_matches(article, markets)  # 모듈 내부 도메인 규칙
    ...
```

---

## MSA 전환 시: 무엇이 사라지고 무엇이 남나

| 요소 | 소속 문서 | MSA 전환 후 |
|---|---|---|
| `domain/`, `application/`의 로직 | `ddd.md` | 그대로 각 서비스 내부에 남음, 거의 안 바뀜 |
| `public.py`의 DTO 정의 | `modular-monolith.md` | REST 스키마로 **승격** (제거 아님) |
| `public.py`의 핸들러 함수 | `modular-monolith.md` | FastAPI 라우터가 그대로 호출 |
| `MessageBus` (호출부 코드) | `modular-monolith.md` | 그대로 유지, 내부 구현만 로컬 함수 → HTTP client로 교체 |
| import-linter "모듈 간 독립성" 계약 | `modular-monolith.md` | **삭제 가능** — 네트워크가 물리적으로 강제해줌 |
| import-linter "모듈 내부 계층" 계약 | `ddd.md` | **그대로 유지** — 서비스가 몇 개로 쪼개지든 각 서비스 내부에서 계속 유효 |

```python
# Before (모듈러 모놀리스)
article = message_bus.dispatch(GetArticleSummary(article_id=command.article_id))
# → 로컬 함수 호출, 밀리초 미만

# After (MSA — News가 별도 서비스로 분리됨)
article = message_bus.dispatch(GetArticleSummary(article_id=command.article_id))
# → 호출부 코드는 동일! MessageBus 내부 구현만 HTTP client로 교체됨
```

News 쪽에서는 `public.py`가 그대로 라우터가 된다:

```python
# services/news/presentation/api.py — public.py가 승격된 것
@router.get("/articles/{article_id}/summary")
def get_article_summary(article_id: str):
    return handle_get_article_summary(GetArticleSummary(article_id=article_id))  # 기존 핸들러 재사용
```

**`Article` 엔티티 자체를 다른 모듈에 노출한 적이 없고, 직렬화 가능한 DTO(`GetArticleSummary`)만 노출했기 때문에 이 전환이 매끄럽다.** 만약 Matching이 `Article` 엔티티를 직접 참조했다면 네트워크로 보낼 수 없어 MSA 전환 시 처음부터 다시 설계해야 했을 것이다.

---

## 한 줄 정리

- **`ddd.md`**: 모듈이 1개든 10개든, 코드가 프레임워크/DB에 오염되지 않게 지키는 **수직** 규칙
- **`modular-monolith.md`**: 계층이 몇 개든, 도메인이 다른 도메인의 구현을 직접 알지 못하게 지키는 **수평** 규칙
- **`integration.md` (본 문서)**: 모듈마다 두 규칙을 겹쳐 걸고, `main.py`를 유일한 조립 지점으로 고정하며, MSA 전환 시 수평 규칙(코드 레벨 강제)은 네트워크로 대체되고 수직 규칙(계층 구조)은 그대로 남는다는 것을 명시
