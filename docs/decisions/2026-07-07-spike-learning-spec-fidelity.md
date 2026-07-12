# ADR: Spike-Learning-Spec Fidelity — Learning 정밀도 기준

**Status**: Accepted
**Date**: 2026-07-07
**Related**: PR #22 (news-collection bootstrap)

---

## Context

**PR #22 에서 발견된 문제**:

Spike (TheNewsAPI 상세 테스트) → Learning (결과 정리) → Spec (구현 설계) 단계를 거쳤으나, **구현 시 Spec 이 불완전해서 API 엔드포인트 오류 발생**:

- Spike: `/v1/news/top` (정확함)
- Spec: (명시되지 않음, 구현자 추정)
- 구현: `/v1/news` 사용 (오류)
- 발견: Integration test 후 (Real API test 추가 시점)

### Root Cause

Spike 임시성 원칙:
- Spike 코드는 버림 ✅
- Learning 정리함 ✅
- **Spec에 Learning 100% 반영하지 않음** ❌

결과: Learning → Spec 전이 불완전 → 구현자가 세부사항 놓침

## Options Considered

### A. Spike 永続化 (Spike 를 참조 가능하게)
- Pros: 구현자가 spike 직접 참조 가능
- Cons: Spike 임시성 위반, 기술부채 (2개 source of truth)

### B. Learning 대강 쓰고 구현 중 "스파이크 다시 보기"
- Pros: 빠름
- Cons: 반복, 수고로움, Spike 버린 의미 없음

### C. Learning 정밀하게 + Spec에 정밀히 반영 (추천) ✅
- Pros: Spike 임시성 지킴, Spec 완전
- Cons: Learning 작성 시간 추가

## Decision

**C - Learning 정밀도 강화 + Spec 반영 기준 명시**

### 1. Learning 작성 기준 (concenews-backend/docs/spike-process.md)

Spike 후 Learning.md 작성 시:
```markdown
## API 응답 구조 (모든 시도 기록)

Tested endpoint:
- GET /v1/news → 404 (작동 안 함)
- GET /v1/news/top → 200 ✅

Query parameter:
- q=keyword → 400 (invalid param)
- search=keyword → 200 ✅

Response JSON:
{
  "data": [
    {
      "title": "...",
      "url": "...",
      "source": "String or {name: String}",  ← type variation
      "publishedAt": "ISO8601Z",  ← UTC
      "description": null  ← nullable
    }
  ]
}
```

**기준**: Spike 코드 버린 후라도 Learning만 읽고 정확히 구현 가능해야 함.

### 2. Spec 반영 체크리스트 (vertical-slices.md)

Spec 작성 단계에서:
```
□ Learning.md 내용 90%+ 반영
  └─ API endpoint (URL, method)
  └─ Query/body 매개변수
  └─ Response 구조 (concrete JSON example)
  └─ Edge case (type variation, nullable 등)
  └─ External dependency (version, env var)

판정: Spec만 읽은 구현자가 정확히 구현 가능
```

### 3. 이점

- **Spike 임시성 지킴**: 코드 버림, 지식만 유지
- **구현 명확**: Spec이 자족적 (Learning 선택 참고용)
- **재발 방지**: 다음 spike에서도 같은 패턴 재사용
- **팀 스케일**: Learning 정밀도 규칙화 → 모두 같은 품질 기대

## Rationale

**Spike의 의도**:
- 학습용 throwaway code (버림)
- 학습 결과만 남김

**현재 문제**:
- Learning이 대강 정리되면, Spec도 대강
- 구현자는 "Spec이 애매하니 코드로 학습" → 효율성 ↓

**해결**:
- Learning을 "Spec 기초"로 정밀하게
- Spec을 Learning을 충실히 반영해 정밀하게
- Spike 버렸지만 지식은 100% 이관

## Reconsider When

- **Learning 형식화 부담**: Learning 작성 시간 > 이득 → 별도 학습 phase 도입 재검토
- **Spike 빈도 ↑**: 매 slice마다 spike → learning 자동화 도구 검토 (OpenAPI, API testing 프레임워크)
- **팀 성숙도**: Learning 품질 일관성 못 유지 → code review guidelines 강화

## Migration Path

### 다음 Spike (news-retrieval 또는 마켓-매칭)

1. **Spike 구현** (기존대로)
2. **Learning 작성** (정밀도 기준 준수)
   - Concrete example (API response, edge case)
   - 모든 시도/실패 기록
3. **Spec 작성** (Learning 90%+ 반영)
   - 체크리스트 사용
4. **Spike 폴더 삭제** (Learning만 유지)

## References

- [vertical-slices.md § 3.1 Learning → Spec 정밀도 규칙](../../concenews-backend/docs/architecture/principles/vertical-slices.md)
- [spike-process.md](../../concenews-backend/docs/spike-process.md) (spike-learning 기준 추가 예정)
- PR #22 회고: spike 결과 (endpoint /v1/news/top) vs 구현 (/v1/news)

---

## Appendix: 이번 news-collection 에서 배운 점

**Spike 결과** (learning-news-api.md 예상):
```
Endpoint: https://api.thenewsapi.com/v1/news/top
Query: search (not q)
Response: {"data": [...], not "articles"}
```

**Spec 부재** → 구현 오류 → Real API test 추가 후 발견

**개선 후**:
- Spec 에 위 내용 명시
- 구현자 "Spec 만 읽고" 정확히 실행 가능
- Real API test 는 Spec 검증용 (첫 번째 test 아님)
