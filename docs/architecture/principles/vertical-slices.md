# Vertical Slice 기반 개발 워크플로우

> Specification-Driven Development (SDD) + Walking Skeleton/Outside-In TDD를 결합한 개발 단위 워크플로우
> concenews 모든 서브레포 적용 가능

---

## 1. Vertical Slice란

**Horizontal 방식** (계층별 완성):
```
1주차: 모든 기능의 Endpoint 다 만들기
2주차: 모든 기능의 Service 다 만들기
3주차: 모든 기능의 Repository 다 만들기
→ 마지막 단계까지 동작하는 기능 없음
```

**Vertical Slice 방식** (기능별 전 계층):
```
1주차: "뉴스 조회" 기능 전체 (Endpoint+Service+Domain+Repo)
2주차: "마켓 매칭" 기능 전체
→ 각 주마다 작지만 실제 동작하는 기능 생김
```

**이점**:
- 통합 리스크 빨리 발견 (Horizontal은 마지막에야 발견)
- 배포 가능한 단위로 작업 (1주 = 1 deliverable)
- 프로덕트 진행 상황 명확 (50% = 기능 절반, 아니라 기능 1개 완성)

---

## 2. 전체 설계 페이즈

**0단계**: constitution.md (프로젝트 불변 원칙) — 1회만
**1단계**: spec.md — 무엇을 만들 것인가
**2단계**: plan.md — 접합부 설계 (Port/Domain/Endpoint 시그니처)
**3단계**: tasks.md — Inside-out 구현 순서 (Domain → Repository → Service → Wire-up)
**4단계**: Acceptance Test 1개 — Slice 완료 판정 (walking skeleton criterion)
**5단계**: Inside-Out TDD — 각 계층 unit test 로 설계
**6단계**: Wire up + 추가 Integration Test (fixture 로 상태 통제)

**Walking Skeleton (선택)**: 복잡한 다중 의존성 있을 때 stub 뼈대 먼저

**핵심**: Acceptance Test 는 spec 에서 곧바로 나옴 (사용자 관점 1개).
Detail 검증 integration test 는 fixture 확보 후 (repository 구현 후).

---

## 3. Spike vs Proper Implementation

**Spike** (학습 단계):
```
spikes/{topic}/
├── approach_1.py
├── approach_2.py
└── LEARNINGS.md ← 핵심 발견만 기록

(로컬만, Git 커밋 X)
```

학습 후 → **learning.md** (정밀한 학습 문서) → spec.md에 반영 → spikes/ 폴더 삭제

**Proper Implementation**:
```
테스트 포함, Git 커밋, 코드 리뷰 준비됨
```

---

## 3.1 Learning → Spec 정밀도 규칙

Spike 코드는 버리지만, **Learning 내용은 완벽히 Spec에 반영해야 함**.

**Learning 작성 (Spike 직후)**:
- Concrete example: 실제 API 응답, 매개변수 등
- 모든 시도/실패: "endpoint A 404, B 200" 식으로
- Edge case: 발견한 모든 이상 (type variation, optional field 등)
- 왜: Spec 단계에서 90%+ 반영 가능해야 함

**예시** (Learning.md):
```markdown
## TheNewsAPI 통합 학습

**Endpoint 테스트**:
- GET /v1/news → 404 ❌
- GET /v1/news/top → 200 ✅

**Query Parameter**:
- q=keyword → 작동 안 함 (400)
- search=keyword → OK

**Response 구조**:
{
  "data": [...],  // NOT "articles"
  "publishedAt": "2026-07-06T10:00:00Z",  // UTC, timezone-aware
  "source": "Bloomberg"  // 가끔 {"name": "X"} dict
}
```

**Spec 반영 체크리스트**:
- [ ] API Endpoint (정확한 URL, HTTP method)
- [ ] Query/Body 매개변수 (이름, 타입, 필수 여부)
- [ ] Response 구조 (key name, field type, nullable)
- [ ] Edge case (source type variation, missing field 등)
- [ ] 외부 dependency 버전 (라이브러리, API v, 환경변수)

**판정 기준**: Spec 읽은 구현자가 "Learning 내용" 없어도 정확히 구현 가능 (Learning은 참고용, 강제 아님).

---

## 4. Slice 크기 판단

**경계 기준**:
- 사용자 관점에서 "완결된 기능"인가?
- 혼자 구현 가능한 크기인가? (1-3일)
- 배포하면 기능이 동작하는가?

**예시**:

| 역할 | Slice | 이유 |
|------|-------|------|
| ✅ 좋음 | "RSS 피드 조회" | 사용자 행동 1개, 기능 완결 |
| ✅ 좋음 | "뉴스-마켓 매칭" | Core Domain, 완독립 |
| ❌ 너무 작음 | "뉴스 엔티티 만들기" | 기능 아님, 준비 작업 |
| ❌ 너무 큼 | "뉴스 조회 + 캐싱 + 실시간 업데이트" | 3주 작업, 나누기 |

---

## 5. Slice 단계별 체크리스트

```
□ 1. Spec (사용자 관점 정의)
  └─ AC 모두 명시되었나?

□ 2. Plan (접합부 설계)
  └─ Endpoint, Domain, Repository 시그니처 결정?

□ 3. Tasks (Inside-out 순서)
  └─ Domain → Repository → Service → Wire-up?

□ 4. Acceptance Test (RED)
  └─ endpoint 200 + schema 유효 1개만? 실패 확인?

□ 5. Stub Green
  └─ endpoint 최소 응답 하드코드로 acceptance test 통과?

□ 6. Inside-Out Unit TDD
  └─ Domain unit test → 구현 → Green
  └─ Repository unit test → 구현 → Green
  └─ Service unit test → 구현 → Green

□ 7. Wire up + Integration Test 추가
  └─ endpoint 를 실제 계층에 연결, acceptance 여전히 green
  └─ 추가 integration test (fixture 로 filled/empty repo 상태 통제)

□ 8. Self-Review & Refactor
  └─ diff 읽고 명확한가? 복잡도 없나?

□ 완료
  └─ 모든 테스트 Green, PR Ready
```

---

## 5.1 테스트 서술 규칙 (GWT)

모든 테스트 docstring 은 **Given-When-Then** 형식.

**Given 은 명시적**:
- 상태 가정은 fixture 로 표현 (`filled_repository`, `empty_repository`)
- 같은 fixture 로 서로 상반된 상태 가정 = 안 됨
- Acceptance test 도 GWT — walking skeleton 은 Given 이 얇을 뿐 생략 아님

```python
# ✅ 좋음: Given 명시
def test_get_news_returns_sorted(client_with_filled_repo):
    """Given: repository 에 news 3개 / When: GET /news / Then: published_at desc"""

# ❌ 나쁨: Given 암묵
def test_get_news_returns_sorted(client):
    """뉴스는 정렬된다"""  # 어떤 상태에서? fixture 없음
```

---

## 6. Plan 단계 — 최소 추정으로 충분

**BDUF(Big Design Up Front) 함정 회피**:

| 결정 필수 | 구현 후 결정 가능 |
|----------|------------------|
| Port 메서드 시그니처 | SQL 쿼리 디테일 |
| Domain Model 필드 | 밸리데이션 규칙 |
| Endpoint 경로/응답 형태 | 페이지네이션, 캐싱 |

Plan에서 100% 확정하려다 보면 설계 페이즈만 길어짐. 대신:
1. "일단 이 정도면 동작할 것" 추정
2. Walking Skeleton 코드하면서 학습
3. 필요하면 plan 다시 다듬기 (normal리팩터링)

---

## 7. Integration Test 속도 관리

병목은 async 여부가 아니라 **무엇을 진짜로 띄우는가**:

| 기법 | 효과 |
|------|------|
| 컨테이너/앱 재사용 (session-scoped) | Postgres 세션 전체 1번만 기동 |
| 트랜잭션 롤백 (function-scoped) | 테스트마다 재기동 대신 롤백 |
| 테스트 피라미드 준수 | Integration은 소수, 나머지는 Unit (Fake 기반) |

---

## 8. 요약: 1인 관점

Vertical Slice는 **"한 주마다 배포 가능한 기능 1개"** 전략.

주간 리듬:
```
월: Spec 확정
화-목: Slice 구현 (TDD 사이클)
금: Refactor + Self-Review
```

→ 매주 1 deliverable. 팀 확장해도 같은 구조로 스케일.
