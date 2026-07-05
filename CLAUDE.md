# CLAUDE.md

## 커밋 컨벤션

### 형식

```
{GITMOJI}{type}: {title}

{description}

- {detail}
- {detail}
```

### 규칙

- gitmoji는 type에 붙여서 작성 (`✨feat`, `🐛fix`)
- description 필수
- `-` 항목은 선택 (복잡한 작업만, 단순 작업은 title + description으로 충분)

### Gitmoji 매핑

| type     | gitmoji | 설명                           |
| -------- | ------- | ------------------------------ |
| feat     | ✨      | 새로운 기능 추가               |
| fix      | 🐛      | 버그 수정                      |
| refactor | ♻️    | 코드 리팩토링 (기능 변경 없음) |
| docs     | 📝      | 문서 추가/수정                 |
| test     | 🧪      | 테스트 추가/수정 (설계 포함)   |
| chore    | 🔧      | 빌드, 의존성, 설정 변경        |

### 예시

**복잡한 작업:**

```
✨feat: 뉴스 카드 컴포넌트 추가

뉴스 목록 페이지에서 각 기사를 표시하는 카드 UI 구현

- 썸네일, 제목, 요약, 날짜 필드 포함
- 클릭 시 상세 페이지로 라우팅
- 모바일 반응형 레이아웃 적용
```

**단순 작업:**

```
🔧chore: 환경 변수 설정 추가

.env.example 파일 추가 및 README에 설정 가이드 작성
```

---

## 언제 무엇을 볼까

| 상황 | 문서 |
|------|------|
| 커밋 메시지 형식 | 이 파일 위 (커밋 컨벤션) |
| PR 만들 때 (단위/브랜치명/master green 규칙) | [git-workflow.md](docs/git-workflow.md) |
| PR 생성 체크리스트 (milestone/label/template) | [github-strategy.md § PR 생성 체크리스트](docs/github-strategy.md) |
| PR 리뷰 (severity, nit 상한, 저자 응답 형식) | [review-standard.md](docs/review-standard.md) |
| Issue / Milestone / Label | [github-strategy.md](docs/github-strategy.md) |
| 새 slice 시작 (Spec/Plan/Task 순서) | [vertical-slices.md](docs/architecture/principles/vertical-slices.md) |
| TDD 순서 헷갈림 (Red-Green-Refactor, GWT) | [xp.md](docs/architecture/principles/xp.md) |
| 도메인 계층 애매 (4계층 어디에?) | [ddd.md](docs/architecture/principles/ddd.md) |
| 새 모듈 폴더 위치 & 경계 | [modular-monolith.md](concenews-backend/docs/architecture/modular-monolith.md) |
| 백엔드 slice 세부 설계 | `concenews-backend/docs/plan-{slice}.md` |
| Docstring 형식 (Google style) | [docstring.md](concenews-backend/docs/conventions/docstring.md) |
| Domain immutability (frozen, tuple 등) | [immutability.md](concenews-backend/docs/conventions/immutability.md) |
| 테스트 구조 & 파일 위치 (unit/integration/acceptance) | [testing.md](concenews-backend/docs/conventions/testing.md) |
| ADR (아키텍처 결정 이력) | [docs/decisions/](docs/decisions/) — index: [README](docs/decisions/README.md) |
| ADR 프로세스 (언제/어떻게 쓰나) | [adr-process.md](docs/adr-process.md) |
| Spike 프로세스 | [spike-process.md](concenews-backend/docs/spike-process.md) |

---

## UV 명령 실행

프로젝트 루트에서 백엔드 명령 실행:

```bash
# 테스트
uv --directory concenews-backend run pytest

# 개발 서버
uv --directory concenews-backend run python -m uvicorn src.main:app --reload

# 기타 Python 스크립트
uv --directory concenews-backend run python script.py
```

또는 백엔드 폴더로 이동 후:
```bash
cd concenews-backend
uv run pytest
uv run python -m uvicorn src.main:app --reload
```

---

## 프론트엔드 설계

사용자는 프론트엔드 미경험. 모든 프론트엔드 작업에서:

- **프론트엔드 엔지니어 입장에서 생각**
- 백엔드 도메인 구조 → 프론트 아키텍처 매핑
- Vue 컴포넌트 설계, 상태 관리 (Pinia) 구조 제안
- 사용자에게 "왜 이렇게 설계하는가" 설명
