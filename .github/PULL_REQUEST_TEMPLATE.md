## 개요

이 PR의 목표를 한 문장으로.

## 주요 변경사항

- 변경 1
- 변경 2
- 변경 3

## 테스트 계획

### 실행한 테스트
```bash
just check-branch-green
```

### 결과
- [ ] 모든 테스트 통과
- [ ] 새 테스트 추가됨
- [ ] 기존 테스트 영향 없음

## 검수 목록

- [ ] 코드 명확한가?
- [ ] 테스트 충분한가?
- [ ] 문서 업데이트되었나?
- [ ] **설계 결정 trigger 매칭 시 ADR 있는가?** ([process](../docs/adr-process.md))
- [ ] **Docs (spec/plan) 에서 관련 ADR 링크 명시됨?**
- [ ] `just check-branch-green` 통과?

## 관련 이슈

## Self-review

- [ ] 현재 Task 범위와 `origin/master...HEAD` diff가 일치한다.
- [ ] 테스트가 요구 계약을 실제로 증명한다.
- [ ] 실제 외부 서비스 요청은 Fake·fixture·격리된 경계로 대체했다.
- [ ] self-review finding을 PR 생성 전에 조치하고 검증을 다시 실행했다.
- [ ] readiness·timeout·cleanup을 확인했고, 고정 sleep만으로 성공을 판정하지 않는다.
- [ ] 컨테이너·운영 변경이면 secret·healthcheck·signal·restart를 확인했다.

### Slice Issue

Related to #00

- 일반 Task PR은 반드시 Slice Issue를 `Related to #번호`로 연결한다.
- Slice의 완료 조건을 모두 충족하는 마지막 Task PR만 `Fixes #번호`를 사용한다.
- Epic Issue는 Task PR에 직접 닫지 않는다.

## 추가 노트

필요하면 추가
