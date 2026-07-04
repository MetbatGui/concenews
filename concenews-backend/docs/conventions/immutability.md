# Domain Immutability 정책

> Pydantic v2 기반. `frozen=True` 의 한계 + 컨테이너 타입 대응.

---

## 원칙

Domain (Aggregate) 모델은 생성 시점부터 identity/state 고정.

- **Attribute 재할당 방지**: `model_config = ConfigDict(frozen=True)`
- **컨테이너 mutation 방지**: 컨테이너 타입 자체를 immutable 로 선언

---

## `frozen=True` 의 한계

```python
class NewsItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    categories: list[str] = Field(default_factory=list)

item = NewsItem(categories=["a"])
item.categories = ["b"]        # ❌ ValidationError (frozen 이 막음)
item.categories.append("b")    # ✅ 통과 (mutation 안 막음)
```

**`frozen=True` 는 얕은 immutability**. 컨테이너 내부 mutation 은 별도 대응 필요.

---

## 필드 타입 정책

| 원본 타입 | Immutable 대체 | 근거 |
|-----------|---------------|------|
| `list[T]` | `tuple[T, ...]` | Stdlib. Pydantic 자동 변환 (list 입력 → tuple 저장). |
| `set[T]` | `frozenset[T]` | Stdlib. Pydantic 자동 변환. |
| `dict[K, V]` | 우선 typed fields 로 분해. 정말 필요 시 `frozendict` (external). | dict 는 대부분 typed field 로 나눌 수 있음 (DDD). |
| `str`, `int`, `float`, `bool`, `datetime`, `Decimal`, ... | 원시 타입 그대로 | 이미 immutable. |

---

## Dict 상세

**대부분의 dict 는 typed fields 로 분해 가능**:

```python
# ❌ 지양
class NewsItem(BaseModel):
    metadata: dict[str, str]

# ✅ 권장
class NewsItem(BaseModel):
    author: str | None
    publisher: str | None
    edition: str | None
```

**정말 dict 가 자연스러운 경우** (동적 키, feature flags 등):
- `frozendict` (외부 package) — 완전 immutable
- `types.MappingProxyType` (stdlib) — read-only view (얕은 immutability, 원본 dict 노출 시 mutable)

이 프로젝트는 현재 dict 필드 없음. 필요해질 때 재검토.

---

## DTO (Response) 는 다름

DTO 는 JSON 직렬화 계약. `list[str]` 유지 (JSON array 자연 대응).

```python
# Domain (immutable)
class NewsItem(BaseModel):
    model_config = ConfigDict(frozen=True)
    categories: tuple[str, ...] = ...

# DTO (mutable, JSON friendly)
class NewsItemResponse(BaseModel):
    categories: list[str] = ...
```

**Pydantic 자동 변환**: Domain `tuple` → JSON `array` → DTO `list`. Boilerplate 없음.

---

## Test 패턴

```python
def test_field_stored_as_immutable_tuple(self):
    """categories 는 immutable tuple 로 저장된다.

    Given: list 입력
    When: NewsItem 생성 후 접근
    Then: tuple 타입, 순서 유지
    """
    item = NewsItem(..., categories=["a", "b"])
    assert isinstance(item.categories, tuple)
    assert item.categories == ("a", "b")


def test_attribute_reassignment_rejected(self):
    """생성 후 attribute 재할당은 거부된다.

    Given: 생성된 인스턴스
    When: 필드 mutation (item.title = "new")
    Then: ValidationError
    """
    with pytest.raises(ValidationError):
        item.title = "new"
```

---

## 참고

- Pydantic v2 `ConfigDict(frozen=True)` — attribute 재할당만 방지
- Python stdlib: `tuple`, `frozenset`, `types.MappingProxyType`
- 외부: `frozendict` package (dict 필요 시)
