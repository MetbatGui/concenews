# ADR: Timezone 정책 — KST 저장 + AwareDatetime 강제

**Status**: Accepted
**Date**: 2026-07-05
**Slice**: Cross-cutting (Domain 정책)

---

## Context

`NewsItem.published_at: datetime` 은 timezone 강제하지 않음. Pydantic v2 는 입력 문자열에 tz 정보가 있으면 aware 로, 없으면 naive 로 파싱.

**잠재 버그**:
- Naive + aware 비교 시 `TypeError`
- Naive 저장 시 원 tz 정보 손실 → 의미 모호
- 여러 source (US API, KR RSS 등) 혼재 시 정렬 오류 가능

Slice 리뷰 (news-fetch) 에서 `data.py` 와 test helpers 의 timezone 스타일 혼재 지적됨.

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| A. `datetime` 그대로 (naive 허용) | 없음 | 실런트 버그, 정렬 실패 |
| B. `AwareDatetime` only (any tz) | Naive 거부, 명확 | KR 유저 표시 시 변환 필요 |
| **C. `AwareDatetime` + KST 정규화** | KR 유저 무변환, 명시적 계약 | 국제화 시 재검토 필요 |
| D. `AwareDatetime` + UTC 저장 (전통) | 국제 표준 | KR 유저 표시 시 매번 변환 |

## Decision

**C: `AwareDatetime` + KST 저장 정규화**.

- **Domain**: `published_at: AwareDatetime` (Pydantic v2, naive 거부)
- **저장 tz**: KST (`timezone(timedelta(hours=9))`)
- **Adapter**: 외부 source (UTC 등) → KST 변환 후 Domain 생성
- **DTO Response**: KST 유지 (JSON 은 `"...+09:00"` 자동 직렬화)

### KST 상수 위치
`src/shared_kernel/time.py` (미래 shared kernel 도입 시)
지금은 news 모듈 로컬 (Rule of Three: 두 번째 모듈에서 tz 필요 시 이전)

## Rationale

- **AwareDatetime 강제**: Naive 거부 → silent bug 원천 차단
- **KST 저장 선택**: Korean 유저 대상 portfolio, 표시 시 무변환
- **Adapter 책임**: 소스별 tz 지식은 adapter 가 소유. Domain 은 계약만 강제.
- **정렬 안전**: 모든 aware datetime 은 비교 가능 (tz 무관)

## Reconsider When

- **국제화 요구** (다국어 유저) → UTC 저장 + 유저별 tz 변환 재검토
- **다중 tz source** 혼재 심각 → shared_kernel time utility 추출
- **Aware vs Naive 관리 오버헤드** 예상 밖으로 큼 → UTC 저장으로 전환

## Migration Path

지금 코드:
- `NewsItem.published_at: datetime` → `AwareDatetime`
- `NewsItemResponse.published_at: datetime` → `AwareDatetime`
- Test fixture (`data.py`): `tzinfo=timezone.utc` → `tzinfo=KST`
- Test string 값 (`"...Z"`) 유지 (Pydantic 이 aware 로 파싱 → validation 통과)

미래 external API adapter (news-collection slice):
```python
KST = timezone(timedelta(hours=9))

# API 응답 (UTC) → KST 변환 후 Domain 생성
utc_dt = datetime.fromisoformat(api_response["published_at"])
kst_dt = utc_dt.astimezone(KST)
NewsItem(published_at=kst_dt, ...)
```

## References

- Pydantic v2 `AwareDatetime` — https://docs.pydantic.dev/latest/api/types/#pydantic.types.AwareDatetime
- Slice 리뷰: `news-fetch` (2026-07-05)
- 관련: [id-strategy-uuidv7](./2026-07-05-id-strategy-uuidv7.md)
