# XP 원칙 — 1인 개발 & 실무 최적화

> Vertical Slice + Walking Skeleton + Outside-In TDD를 실행하기 위한 Extreme Programming 선택적 도입
> 1인 개발을 가정하되, 팀 확장 시 그대로 스케일하는 구조

---

## 1. 왜 XP인가

**Traditional Waterfall의 문제** (spec → plan → code → test):
- 테스트가 마지막 → 버그 발견이 늦음
- 요구사항 변경 시 대가 큼
- 1인 개발에선 코드 리뷰 없음 → 품질 검증이 테스트에만 의존

**XP의 해법**:
- TDD로 불확실성 감소 (Red-Green-Refactor)
- Simple Design로 복잡도 통제 (Ponytail 정신)
- Refactoring을 continuous로 (debt 누적 방지)
- Self-Review로 Pair Programming 효과 (1인 모드)

---

## 2. 1인 개발에 최적화된 5가지 프랙티스

### 2.1 TDD — Test-First, Uncertainty-Driven

**원칙**: 구현 전에 테스트부터. 이유: 1인 개발에선 코드 리뷰가 없으므로 테스트 ≈ 품질 검증 유일한 기준.

**실행 방식** (Red-Green-Refactor):

```
Red   : 실패하는 테스트 작성 (요구사항 명시)
Green : 최소 코드로 테스트 통과
Refactor : 불필요 복잡도 제거, 설계 개선
```

**1인에게 필요한 3가지**:

| 테스트 유형 | 역할 | 서술 예 |
|-----------|------|--------|
| Unit (Fake) | 비즈니스 로직 → 빠른 검증 | `test_match_score_above_threshold_returns_true` |
| Integration | 계층 경계 계약 → Slice 완료 기준 | `test_get_news_returns_articles_from_db` |
| E2E | 외부 서비스 연동 → 배포 전/주기적 | `test_fetch_rss_and_store_news` (`@pytest.mark.e2e`) |

**실무 간극** ("완벽한 TDD"는 불가능):

```python
# Spike (학습 단계) — 테스트 불필요
def spike_explore_matching_algorithm():
    # 빠르게 복수 알고리즘 시도, 성능 확인
    # 학습 후 버린다
    pass

# Proper Implementation (결정 후) — 테스트 필수
class MatchingPolicy(BaseModel):
    def match(...) -> Match:
        # Unit + Integration 테스트 포함
        pass
```

**기준**: "나중에 고칠 것 같은 부분 = 테스트 필요". Spike와 결정 사이에 명확한 commit message로 구분.

### 2.2 Simple Design — Ponytail 정신

**원칙**: 지금 필요한 것만. 투기적 추상화 금지.

**체크리스트**:

- [ ] stdlib/네이티브 기능 먼저? (예: `@lru_cache` vs 커스텀 캐시)
- [ ] 하나의 구현만 필요한가? (Factory, Strategy 패턴 제거)
- [ ] 이 인터페이스는 진짜 필요한가? (Adapter는 수정 시에만)
- [ ] 설정값인가, 하드코드인가? (설정 파일은 현재 사용 변수만)

**예시** (나쁜 예시 수정):

```python
# ❌ 투기적 설계 (future-proofing)
class RepositoryFactory:
    @staticmethod
    def create(db_type: str) -> BaseRepository:
        if db_type == "postgres":
            return PostgresRepository()
        elif db_type == "mysql":
            return MySQLRepository()

# ✅ Simple Design (지금 필요: Postgres만)
class NewsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    # MySQL 필요하면 그때 리팩터링
```

---

### 2.3 Refactoring — 매 커밋 전 한 번

**원칙**: Smoke test (빌드/테스트) 통과 후, merge 전에 자신의 코드를 한 번 더 읽기.

**체크리스트**:

- [ ] 변수명이 명확한가? (`d` → `match_score`)
- [ ] 함수가 한 가지만 하는가? (15줄 넘으면 의심)
- [ ] 중복 코드가 있는가? (3줄 반복 = 추출 신호)
- [ ] 테스트가 의도를 드러내는가? (단순 assert만으로 충분?)
- [ ] Docstring이 WHY를 말하는가? (WHAT은 코드가 말함)

**1인 모드에서의 Self-Review**:

```python
# 커밋 전 자신의 diff를 읽기
git diff HEAD~1

# 질문하기:
# "여기 왜 이렇게 짰지?"
# → 명확한 답이 없으면 리팩터링 신호
```

---

### 2.4 Self-Review — Pair Programming 대체

**원칙**: Pair Programming은 1인 때 불가능하지만, 코드 리딩은 가능.

**실행 방식**:

1. **기능 구현 후 며칠 뒤 읽기** — 컨텍스트 망각 후 읽으면 남의 코드처럼 느껴짐 (객관성 확보)
2. **Diff로 읽기, 전체 파일로 읽지 않기** — diff만 봐야 의도가 두드러짐
3. **의문 기록** — "여기 왜?" 의문이 없으면 good, 있으면 개선 기회

**체크리스트**:

- [ ] 이 변수는 왜 필요한가?
- [ ] 이 if 분기는 정말 필요한가? (가드절로 단순화 가능?)
- [ ] 테스트가 실제로 검증하는가? (테스트 통과 = 실제 동작이 아닐 수도)
- [ ] 나중에 누군가 이 코드를 읽을 때 이해할 수 있을까?

---

### 2.5 Sustainable Pace — 번아웃 방지

**원칙**: 1인 개발의 가장 큰 위험은 속도가 아니라 지속 가능성.

**스프린트 구조** (1주일 단위):

```
월: Spec 확정 (사용자 관점)
화-목: Slice 구현 (TDD 사이클)
금: Refactor + Self-Review + 문서 정리
주말: 휴식
```

**주의사항**:

| 위험 | 신호 | 대응 |
|------|------|------|
| Scope creep | "코드 쓰다 보니 다른 기능도 필요한데?" | Spike로 분리, 별도 Slice로 이슈화 |
| Test fatigue | 테스트 짜는 데 구현 시간 2배 이상 | 불필요한 테스트 제거 (YAGNI applies to tests too) |
| Debt 누적 | "나중에 리팩터링하면 되지" | 매 PR마다 리팩터 (나중은 절대 안 옴) |
| Over-engineering | 투기적 설계 | Simple Design 체크리스트 매 커밋 전 |

---

## 3. Vertical Slice + XP 통합 워크플로우

한 Slice = 한 주기 (1-3일):

```
1. Spec (사용자 관점 정의)
   ↓
2. Test 작성 (Integration + Unit)
   ↓
3. Stub 상태로 테스트 통과 확인 (Green이 되도록 fake 구현)
   ↓
4. Outside-In: 바깥쪽부터 안쪽으로 Stub 교체 (TDD Red-Green-Refactor)
   ↓
5. Self-Review: diff 읽기, 리팩터링
   ↓
6. 모든 테스트 통과 + PR ready → merge
```

**각 단계의 검증 기준**:

| 단계 | 기준 | 넘어가기 전 확인 |
|-----|------|-----------------|
| Spec | 사용자 관점에서 "이게 다인가" | AC(Acceptance Criteria) 모두 명시 |
| Test | Integration Test 실패하는가? | Stub 상태에서 실패 확인 (예: KeyError 말고 AssertionError) |
| Stub | 테스트 통과하는가? | 모든 테스트 green (가짜 구현이지만) |
| Implementation | 진짜 구현 후 테스트 여전히 green? | 같은 테스트, 다른 구현 |
| Refactor | 1인이 읽기에 명확한가? | diff 읽고 "왜?"라는 의문 없음 |

---

## 4. 프론트엔드 + 백엔드 적용

### 4.1 백엔드 (FastAPI/Postgres)

**Slice 예시**: "RSS 뉴스 조회"

```python
# 1. Integration Test (TDD Red)
@pytest.mark.asyncio
async def test_get_news_returns_articles():
    client = AsyncClient(...)
    response = await client.get("/news")
    assert response.status_code == 200
    assert len(response.json()) >= 0

# 2. Stub (Green)
@router.get("/news", response_model=list[NewsArticleResponse])
async def get_news():
    return []  # 가짜 구현

# 3. Implementation (여전히 Green)
@router.get("/news", response_model=list[NewsArticleResponse])
async def get_news(repo: NewsRepository = Depends()):
    articles = await repo.find_all()
    return [NewsArticleResponse.model_validate(a) for a in articles]

# 4. Unit Test (세부 로직)
def test_match_score_calculation():
    match = Match(news=..., market=..., score=0.85)
    assert match.is_relevant(threshold=0.7)
```

### 4.2 프론트엔드 (React/Vitest)

**Slice 예시**: "뉴스 목록 조회 UI"

```typescript
// 1. E2E 테스트 (사용자 관점, Playwright)
test("사용자가 뉴스 목록을 볼 수 있다", async ({ page }) => {
  await page.goto("/news");
  await expect(page.locator("text=뉴스")).toBeVisible();
  await expect(page.locator("[data-testid=news-card]")).toHaveCount(2);
});

// 2. Stub (MSW — Mock Service Worker로 가짜 API)
import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";

const server = setupServer(
  http.get("/api/news", () => {
    return HttpResponse.json([
      { id: "1", title: "뉴스 1" },
      { id: "2", title: "뉴스 2" },
    ]);
  })
);

// 3. Component Test (단위 테스트)
test("NewsCard는 title을 표시한다", () => {
  render(<NewsCard article={{ id: "1", title: "제목" }} />);
  expect(screen.getByText("제목")).toBeInTheDocument();
});

// 4. Integration Test (컴포넌트 + 데이터 페칭)
test("NewsList는 뉴스를 fetch하고 표시한다", async () => {
  const { useNews } = renderHook(() => useNews(), {
    wrapper: ({ children }) => (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    ),
  });

  render(<NewsList />);
  
  await waitFor(() => {
    expect(screen.getAllByRole("article")).toHaveLength(2);
  });
});
```

---

## 5. 실무 예외 & 타협

### 5.1 Spike — 학습 > 테스트

학습 단계에선 테스트 없이 빠르게 시도. 학습 후 결정하면 proper 구현으로.

**Spike 생명주기**:

```
spikes/{topic}/
├── approach_1.py
├── approach_2.py
└── LEARNINGS.md  ← 핵심 발견 기록

↓ (학습 완료)

spec.md 업데이트 (Decision 섹션 추가)

↓

rm -r spikes/{topic}  ← 정리, Git에 남지 않음

↓

✨feat: Cosine 유사도 기반 매칭 알고리즘 채택
(Spike 결과 기록, proper 구현 이후)
```

**예시**:

```python
# 커밋 1: Spike (로컬만)
# 📝Spike: Matching 알고리즘 후보 3개 비교 (spikes/matching_algorithm/)
# 결과: Cosine similarity 최적 (정확도 85%, 속도 100ms)

# 커밋 2: Decision (Git에 기록)
# ✨feat: Cosine 유사도 기반 매칭 알고리즘 채택
# 
# Spike에서 3가지 비교 후 선택:
# - Cosine similarity (TF-IDF) ← 선택
# - Keyword exact match (false positive)
# - LLM embedding (느림)
#
# 선택 근거: 실시간 처리 필요 + 85% recall 충분

# (이후 spikes/matching_algorithm 폴더 삭제)
```

### 5.2 E2E 테스트 — 배포 전 + 주기적

Integration Test (Fake 경계)로 Slice 완료 판정.
E2E (진짜 외부 서비스)로 배포 전/주기적 검증.

```python
# 배포 전에만 실행
pytest -m "not e2e"  # Slice 완료 기준 (CI)
pytest -m "e2e"      # 배포 전 (수동)
```

### 5.3 레거시 코드 — 테스트 없이 시작

레거시 코드 중 수정 부분만 테스트로 보호.
전체 레거시를 테스트하려다 보면 진행 안 됨 (Working Effectively with Legacy Code 참고).

```python
# 레거시 함수 수정할 때만 테스트
@patch('legacy_module.global_state', {})
def test_legacy_function_respects_new_parameter():
    result = legacy_function(new_param=True)
    assert result.status == "ok"
```

---

## 6. 요약: TDD의 3가지 규칙 (1인 모드)

| 규칙 | 1인 모드에서 의미 |
|-----|------------------|
| **Red** | 요구사항 → 테스트로 명시. "뭘 검증할 것인가"를 먼저 결정 (코드 리뷰 없으니 테스트가 유일한 검증) |
| **Green** | 최소 코드 통과. Stub 상태 OK. 복잡도 유치 금지 (나중에 리팩터링할 거라는 핑계 말기) |
| **Refactor** | 매 커밋 전 한 번. 그리고 자신의 코드를 1-2일 뒤에 읽기 (객관성 확보) |

**최종 체크**:
- [ ] 테스트 없이 ship하려는 게 있는가? → 테스트 추가 (Spike 제외)
- [ ] 테스트 짜느라 구현이 10배 오래 걸리는가? → 테스트 범위 축소 (YAGNI)
- [ ] "나중에 리팩터링하면 되지"라는 생각이 드는가? → 지금 당장 리팩터링
- [ ] 코드 읽을 때 "왜 이렇게 짰지?"라는 의문이 있는가? → Self-Review 필요

---

## 7. 참고: XP와 Ponytail의 관계

```
Simple Design = 지금 필요한 것만 (YAGNI)
↑ Ponytail의 핵심

TDD = 미리 생각하고 테스트로 명시
↑ XP의 핵심

둘 다 "복잡도 감소"를 목표로 하지만, 다른 각도:
- Simple Design: "뭔가는 안 쓰자" (삭제 중심)
- TDD: "먼저 검증하고 만들자" (설계 중심)

→ 함께 쓰면 상승효과
```

---

## 8. 실행 체크리스트 (이번 Slice부터)

- [ ] Spec 작성 (사용자 관점, AC 포함)
- [ ] Integration Test 작성 (빨간불이 맞음)
- [ ] Stub으로 green 만들기
- [ ] 실제 구현 (Stub 교체)
- [ ] Unit Test 추가 (세부 로직)
- [ ] Self-Review: diff 읽고 리팩터링
- [ ] 최종 테스트 실행 (local)
- [ ] PR 생성 (머신러닝 리뷰 대신 자신의 리뷰)
- [ ] Merge (테스트 green, diff 명확)

끝.
