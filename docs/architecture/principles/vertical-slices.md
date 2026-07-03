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
**3단계**: tasks.md — Stub 교체 순서 (의존성 역순)
**4단계**: Integration Test 작성 — Slice 완료 판정 기준
**5단계**: Outside-In TDD — 엔드포인트 구현, 점진적 Refactor로 계층 분리

**Walking Skeleton (선택)**: 복잡한 다중 의존성 있을 때만 필요
- 단순 기능: 5단계에서 직접 구현 (가장 프래그마틱)
- 복잡한 기능: 미리 Stub 뼈대로 통합점 검증 후 구현

**핵심**: tasks.md가 Integration Test보다 먼저. 의존성 순서를 알아야 Integration Test 검증 대상이 결정되기 때문.

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

학습 후 → spec.md에 Decision 추가 → spikes/ 폴더 삭제

**Proper Implementation**:
```
테스트 포함, Git 커밋, 코드 리뷰 준비됨
```

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
  └─ AC(Acceptance Criteria) 모두 명시되었나?

□ 2. Plan (접합부 설계)
  └─ Endpoint, Domain Model, Repository 시그니처 결정?

□ 3. Tasks (Stub 교체 순서)
  └─ 의존성 역순 (가장 깊은 것부터 교체)?

□ 4. Integration Test (RED)
  └─ 모든 테스트 빨간불 (아직 구현 안 함)?

□ 5. Outside-In TDD (GREEN → REFACTOR)
  └─ 엔드포인트 구현 (Mock data)
  └─ 테스트 통과 확인
  └─ 점진적 refactor로 계층 분리 (Service → Domain → Repository)
  └─ 각 단계마다 테스트 Green 유지?

□ 6. Self-Review & Refactor
  └─ diff 읽고 명확한가? 복잡도 없나?

□ 완료
  └─ 모든 테스트 Green, PR Ready

**주의**: Walking Skeleton은 복잡한 다중 의존성이 있을 때만 사용. 단순 기능은 5단계에서 직접 구현하는 것이 더 빠르고 프래그마틱.
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
