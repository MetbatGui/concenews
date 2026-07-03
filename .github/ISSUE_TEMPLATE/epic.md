---
name: Epic (Slice)
about: Slice 단위 기능 (전체 계획)
title: "[SLICE] "
labels: "type: epic"
---

## 개요

한 문장으로 Slice 목표.

## 사용자 스토리

**주요 사용자**: 누구인가?

**목표**: 무엇을 할 수 있어야 하는가?

**이유**: 왜 중요한가?

## Acceptance Criteria (AC)

- [ ] AC 1: ...
- [ ] AC 2: ...
- [ ] AC 3: ...

## 기술 검증 (Spike)

### Spike 완료?
- [ ] API/기술 검증 완료
  - 참고: [spikes/LEARNINGS.md](...)
- [ ] 결정된 구현 기술
  - ...
  - ...

### 문제 없음?
- [ ] 성능 OK
- [ ] 비용 OK
- [ ] 의존성 OK

## 구현 계획

### PR 단위 분해

- **PR #N**: Domain 모델
- **PR #N+1**: Repository
- **PR #N+2**: Service
- **PR #N+3**: Endpoint
- **PR #N+4**: Refactor & Test
- **PR #N+5**: Close Epic

### 참고 문서

- Spec: [docs/spec-xxx.md](...)
- Plan: [docs/plan-xxx.md](...)

## 로드맵

완료 후 다음 Slice:
- [ ] Slice-2: ...
- [ ] Slice-3: ...
