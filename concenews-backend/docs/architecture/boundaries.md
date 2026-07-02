

# 계층 간 데이터 타입 경계 원칙 (Layer Boundary Data Contracts)

> concenews 아키텍처 원칙 문서 — `docs/architecture/principles/` 편입 후보
> 배경: Domain Model을 Pydantic으로 채택했을 때, 각 계층 경계에서 어떤 타입을 주고받아야 하는지 정리

---

## 1. 전체 그림

```
Endpoint (FastAPI)          Service (UseCase)           Repository (Infra)
Pydantic Request/Response ←→ Domain Model (Pydantic) ←→ dict ←→ ORM Model
      명확한 타입 유지              명확한 타입 유지        여기만 짧게 dict 허용
```

경계마다 dict 허용 여부가 다르다. 판단 기준은 하나다.

> **dict의 생존 시간(lifetime)이 짧고 소비 지점이 명확하면 OK.**
> **dict가 여러 함수/모듈을 넘나들며 사실상 타입 역할을 하면 안티패턴.**

---

## 2. Domain Model = Pydantic일 때 계층별 영향

### 2.1 Infra 방향 (Domain ↔ ORM) — 거의 신경 쓸 필요 없음

`model_dump()` / `Model(**data)`로 충분하다.

```python
# repository/mapper.py
def to_dict(article: NewsArticle) -> dict:
    return article.model_dump()

def to_domain(data: dict) -> NewsArticle:
    return NewsArticle(**data)  # 생성 시점에 자동 밸리데이션
```

- 예외: ORM 필드명이 Domain과 다르면(`source` vs `source_type`) `model_dump(by_alias=True)` 또는 명시적 변환 필요
- 여기서 쓰이는 dict는 **함수 하나 안에서 생성되고 즉시 소비**되므로 생존 시간이 극도로 짧다 → 안전

### 2.2 API 방향 (Domain ↔ Request/Response) — 새로운 함정 발생

Domain이 Pydantic이 되면 "Request/Response 스키마로 Domain Model을 그대로 써도 되지 않나"라는 유혹이 생기는데, 이건 피해야 한다.

```python
# 위험한 패턴 — Domain Model을 API 응답으로 그대로 노출
@router.get("/news")
async def get_news() -> list[NewsArticle]:
    return await use_case.execute()
```

**위험한 이유**

1. API 계약과 Domain이 결합됨 — Domain에 내부용 필드가 추가되면 자동으로 API 응답에 노출됨
2. concenews의 "모듈 경계, public.py, 스왑 가능성" 원칙과 충돌 — 인터페이스는 안정, 내부는 자유롭게 교체되어야 함
3. API 버저닝 시 Domain Model 자체를 분기해야 하는 상황 발생

**대응**: 얇더라도 별도 Response/Request 스키마를 유지하고 `model_validate()`로 변환한다.

```python
class NewsArticleResponse(BaseModel):
    id: str
    title: str

@router.get("/news")
async def get_news() -> list[NewsArticleResponse]:
    articles = await use_case.execute()
    return [NewsArticleResponse.model_validate(a) for a in articles]
```

---

## 3. dict 사용 판단 기준

### 3.1 dict가 정당한 경우

| 상황                                 | 설명                                                                  |
| ------------------------------------ | --------------------------------------------------------------------- |
| 경계를 넘나드는 짧은 통로(transport) | `to_dict(article) → ORM(**data)`처럼 한두 줄 안에서 즉시 소비      |
| 직렬화 경계(진짜 I/O)                | JSON, 캐시(Redis), 메시지 큐 페이로드 등 원래 구조화 타입이 없는 지점 |

### 3.2 dict가 안티패턴이 되는 경우

| 상황                                | 설명                                                                                                          |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 함수 시그니처에 dict가 오래 머무름  | `def process(data: dict) -> dict` — Primitive Obsession. IDE 자동완성 불가, `KeyError`는 런타임에만 발각 |
| dict 위에서 비즈니스 로직 직접 수행 | `if data["status"] == "active"` — Domain Model이 할 일을 dict가 대신함 (Anemic Domain Model보다 나쁜 형태) |
| 모듈 경계를 넘어 dict가 오래 이동   | 모듈 간 public 인터페이스가 dict면 계약이 코드로 강제되지 않고 런타임에만 깨짐이 발견됨                       |

### 3.3 반례 — 실제 안티패턴 사례

```python
created_user = user_repo.create_user(...)
return {"username": created_user.username, "hashed_pw": created_user.hashed_pw}
```

문제 2가지:

1. **dict가 함수의 계약(contract) 자체가 됨** — 호출부가 `result["username"]`으로 꺼내 써야 하고, 오타는 런타임까지 발각 안 됨
2. **보안 문제** — `hashed_pw`가 리턴값에 노출되면 API 응답까지 이어질 위험 있음. bcrypt 해시라도 외부에 나가면 안 됨

**정정**

```python
created_user: User = user_repo.create_user(...)
return created_user  # Domain Model 그대로 리턴

class UserResponse(BaseModel):
    username: str  # hashed_pw 필드 자체를 선언하지 않음 → 노출 원천 차단

@router.post("/users")
async def create_user(...) -> UserResponse:
    created_user = await use_case.execute(...)
    return UserResponse.model_validate(created_user)
```

---

## 4. Endpoint ↔ Service 경계 — dict 사용 금지

이 경계는 프로젝트에서 **가장 안정적이어야 할 계약**이다. dict를 끼우면 안 되는 이유:

1. **양쪽 다 이미 타입이 존재함** — Endpoint엔 Pydantic Request/Response, Service엔 Domain Model. 타입 없는 매개체를 끼우면 얻는 것 없이 IDE 지원만 잃음
2. **가장 자주 바뀌는 경계** — API 스펙 변경 시 dict면 문자열 키(`"username"`)를 grep해서 찾아야 하지만, 타입이면 IDE/컴파일 단계에서 바로 드러남
3. **mapper의 dict와는 성격이 다름** — mapper의 dict는 함수 하나 안에서 즉시 소비되지만, Endpoint→Service dict는 함수 인자/리턴 타입으로 시그니처에 박제되어 훨씬 오래 산다

**결론**: dict가 안전한 곳은 Infra 경계(mapper.py) 하나뿐. Endpoint↔Service는 Domain Model(Pydantic)을 그대로 주고받는다.

---

## 5. Request/Response 스키마 분리 원칙

### 5.1 원칙 — 용도(Create/Update/Response)마다 분리

같은 리소스라도 엔드포인트(정확히는 "용도")마다 필요한 필드 집합이 다르다.

```python
# POST /users — 생성 시엔 password 입력 필요
class CreateUserRequest(BaseModel):
    username: str
    password: str

# GET /users/{id} — 조회 시엔 password 자체가 없어야 함
class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime

# PATCH /users/{id} — 수정 시엔 모든 필드가 optional
class UpdateUserRequest(BaseModel):
    username: str | None = None
```

하나의 스키마를 세 군데 다 재사용하면 `Optional` 범벅이 되거나, 조회 응답에 `password`가 실수로 살아남는 사고가 나기 쉽다.

### 5.2 중복 줄이기 — 상속으로 공통 필드 분리

```python
class UserBase(BaseModel):
    username: str

class CreateUserRequest(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    created_at: datetime
```

완전 독립도, 완전 재사용도 아닌 중간 지점.

### 5.3 예외

Create/Response 필드가 100% 동일하고(민감 정보 없음, optional 차이 없음) 규모가 작으면 하나로 합쳐도 실용적으로 문제없다. 단, 이건 "필드가 우연히 같다"는 현재 상태에 기댄 것이므로 필드가 갈라지는 순간(비밀번호, 내부 메타데이터 추가 등) 즉시 분리해야 한다.

### 5.4 원칙의 근거 — ISP(Interface Segregation Principle)를 DTO에 적용

> "클라이언트는 자신이 사용하지 않는 메서드/인터페이스에 의존하도록 강요받으면 안 된다." (SOLID, ISP)

이를 데이터 구조에 적용하면:

> "클라이언트(엔드포인트 호출자)는 자신이 쓰지 않는 필드까지 포함된 하나의 거대한 모델에 의존하도록 강요받으면 안 된다."

관련 개념:

- **DTO 패턴** (Martin Fowler, *Patterns of Enterprise Application Architecture*) — 계층 간 전송 데이터는 용도에 맞게 별도 객체로 구성
- **CQS/CQRS적 사고** (느슨하게 관련) — Command(Create/Update)와 Query(Response)를 다른 모델로 다룬다는 관점에서 정신이 통함. 단, 본 원칙은 저장소/모델을 완전 분리하는 CQRS만큼 무겁지 않은 가벼운 버전
- **SRP** — Create 스키마와 Response 스키마는 서로 다른 변경 이유(입력 검증 규칙 vs 출력 필드)를 가지므로 분리되어야 함

공식적으로 이름이 고정된 GoF 패턴은 아니며, 실무에서는 "Request/Response 스키마 분리" 또는 "용도별 DTO 패턴"으로 통칭한다.

---

## 6. 요약

| 경계                         | dict 허용 여부    | 비고                                                          |
| ---------------------------- | ----------------- | ------------------------------------------------------------- |
| Endpoint ↔ Service          | ❌ 금지           | Pydantic Request/Response ↔ Domain Model(Pydantic) 직접 사용 |
| Service ↔ Repository(Infra) | ✅ 짧게 허용      | mapper.py 안에서만, 함수 하나 안에서 생성·소비               |
| Domain ↔ API 응답           | ❌ 직접 노출 금지 | Domain Model 재사용 대신 얇은 Response 스키마 분리            |
| Request/Response 스키마      | 용도별 분리 원칙  | 공통 필드는 Base 클래스 상속으로 중복 최소화                  |
