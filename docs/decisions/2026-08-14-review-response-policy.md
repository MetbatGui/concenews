# ADR: 리뷰 finding 의 처리 주체를 severity 로 결정

**Status**: Accepted
**Date**: 2026-08-14
**Slice**: Cross-cutting

## Context

독립 리뷰 이후 finding 을 누가 처리하는지에 대해 두 문서가 어긋나 있었다.

- [review-standard.md](../review-standard.md) — 🔴 bug / 🟡 risk / ❓ question 에 대해 저자가 `accept`/`defer`/`fix` 를 명시 결정한다.
- [workflow.md](../workflow.md), [git-workflow.md](../git-workflow.md) — Question 이 없으면 Bug·Risk·Nit 을 자동 수정한다.

후자는 커밋 `00afcef` 에서 도입되었으나 `review-standard.md` 가 함께 갱신되지 않아 규칙이 반쪽만 적용된 상태였다. 본 ADR 은 그 도입 결정에 대한 소급 기록을 겸한다 ([adr-process.md § 소급 적용](../adr-process.md)).

더 근본적인 문제는 자동 수정 대상에 🟡 risk 가 포함된 점이다. `review-standard.md` 의 severity 표는 risk 를 **"동작하지만 취약, 결정 필요"** 로 정의한다. 정의가 결정을 요구하는 항목을 결정 없이 자동 처리하면 severity 체계 자체가 무의미해진다.

## Options Considered

| 옵션 | Pros | Cons |
|------|------|------|
| A. 전건 저자 결정 (자동 조치 철회) | 기존 review-standard 유지 | bug·nit 처럼 판단 여지가 없는 finding 까지 대기. 리뷰가 merge 지연 요소가 됨 |
| B. 전건 자동 수정 | 처리 속도 최대 | risk 의 정의("결정 필요")와 모순. 설계 판단이 기록 없이 확정됨 |
| C. 상황별 모드 분리 (평시 수동 / 필요 시 자동) | 두 요구를 모두 수용 | 규칙에 예외 조항이 생김. 발동 조건이 문서 밖 판단에 의존해 재현 불가 |
| D. severity 정의에서 처리 주체를 도출 | 규칙이 기존 정의에서 따라나옴. 예외 없음 | risk 처리 시 사람 개입이 계속 필요 |

## Decision

**옵션 D 채택.** severity 별 처리 주체를 다음과 같이 고정한다.

| severity | 처리 | 근거 |
|---|---|---|
| 🔴 bug | 리뷰어 자동 수정 | 깨진 동작은 `accept` 대상이 아니고 merge 블록이므로 `defer` 도 불가하다. 선택지가 `fix` 뿐이므로 결정할 여지가 없다 |
| 🔵 nit | 리뷰어 자동 수정 | 이미 저자 재량으로 규정되어 있고 기존에도 일괄 accept 였다 |
| 🟡 risk | 사용자 명시적 결정 | 정의가 "결정 필요"다 |
| ❓ question | 사용자 명시적 결정 | 정의가 판단 요청이다 |

자동 수정한 항목은 `# Caveman Review 조치` 댓글에 조치 내용과 검증 결과를 기록한다. 🟡·❓ 는 결정 전에 해당 결정을 전제한 코드를 변경하지 않는다.

## Rationale

처리 주체를 severity 와 독립적으로 정하면 두 체계가 각자 표류한다. `00afcef` 이후 실제로 그렇게 되었다. severity 정의에서 처리 주체를 도출하면 규칙이 하나로 줄고, severity 판정이 곧 처리 방식 판정이 되어 리뷰어가 추가로 판단할 것이 없다.

옵션 C(모드 분리)를 기각한 이유는 두 가지다. 첫째, 발동 조건이 문서 밖 상황 판단에 의존해 같은 입력에 같은 결과가 나오지 않는다. 둘째, 프로세스 문서에 예외 조항이 있으면 규칙 전체의 구속력이 약해진다.

옵션 A 는 [review-standard.md § 근거](../review-standard.md) 의 "리뷰 = merge 지연 요소, 최소화" 원칙과 충돌한다. bug 와 nit 은 판단이 필요 없으므로 대기시킬 이유가 없다.

## Reconsider When

- 🟡 risk finding 이 리뷰당 다수 발생해 병목이 될 때. 그 경우 우선 severity 판정 기준이 느슨한지 검토한다
- 리뷰어가 자동 수정한 bug 에서 오수정이 반복될 때

## References

- [review-standard.md](../review-standard.md) — severity 정의와 저자 응답 규칙
- [workflow.md](../workflow.md) — 10. Self-review와 독립 리뷰
- [git-workflow.md](../git-workflow.md) — 독립 리뷰와 수정 승인
- [adr-process.md](../adr-process.md) — 프로세스 규칙 트리거, 소급 적용
