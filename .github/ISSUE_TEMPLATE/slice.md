---
name: Slice
about: Vertical Slice 단위 이슈 (Spec/Plan 확정 + 사용자 승인 후에만 생성)
title: "[Slice] "
labels: slice
---

## 개요

한 문장으로 Slice 목표.

Spec: <!-- concenews-backend/docs/spec-{slice}.md 링크 -->
Plan: <!-- concenews-backend/docs/plan-{slice}.md 링크 -->
관련 ADR: <!-- 있으면 -->

## Acceptance Criteria

- [ ] AC 1: ...

## Tasks

각 Task는 `.github/ISSUE_TEMPLATE/task.md`로 이 이슈의 서브이슈로 생성한다.

- [ ] #{task-issue-1}
- [ ] #{task-issue-2}

완료: 모든 Task 서브이슈가 닫히고 Integration Test green 확인되면 수동으로 닫는다.
