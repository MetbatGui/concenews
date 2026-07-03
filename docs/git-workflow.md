# Git Workflow

> 1인 개발자 기준, Vertical Slice + XP 프로세스 연계

---

## 브랜치 전략

### main
- 항상 배포 가능 (모든 테스트 green)
- PR 기반 merge (self-review 포함)

### feature/{slice-name}-{task}
```
feature/news-fetch-endpoint-mock   (mock endpoint, 통합테스트 GREEN)
feature/news-fetch-service         (Service 레이어 추출)
feature/news-fetch-domain          (Domain 모델 추출)
feature/news-fetch-repository      (Repository 추출)
feature/news-fetch-close           (Issue close)
```
- **단위**: PR 1개 = 브랜치 1개 (작업 내용 명시)
- master에서 생성, PR merge 후 삭제

---

## Spike (로컬만, Git X)

```
spikes/{topic}/
├── {api}_spike.py
└── LEARNINGS.md
```

**중요**: Spike는 브랜치 불필요
- 로컬 폴더 (.gitignore에 등록)
- commit 안 함
- 학습 후 폴더 삭제
- 결정만 spec.md에 기록

---

## Commit 메시지

[CLAUDE.md 커밋 컨벤션 참고](../CLAUDE.md)

```
🔧chore: 패키지 설치

requirements.txt 업데이트
- pytest>=7.0
- sqlalchemy>=2.0
```

---

## Pull Request

1인이지만 self-review 필수:
```bash
git diff main..feature/news-fetch
# → diff 읽고 refactor 필요 확인
# → 복잡도 없나, 명확한가?
```

PR 체크리스트:
- [ ] 모든 테스트 green
- [ ] diff 명확한가?
- [ ] 불필요한 코드 없나?
- [ ] Integration Test 통과했나?

---

## 병렬 Slice 없음

1인 개발 → 1번에 1 Slice만
- feature/x 진행 중 → feature/y는 안 함
- 완료 후 merge → 다음 Slice로

---

## 요약

| 단계 | 브랜치 | 액션 |
|------|--------|------|
| Spike (학습) | — (로컬) | spikes/{topic}/ → LEARNINGS.md → 삭제 |
| Spec 확정 | master | spec.md commit |
| 개발 | feature/{slice}-{task} | code → test → refactor |
| PR & Review | feature/{slice}-{task} | self-review → merge |
| 배포 | master | 자동화 또는 수동 |

