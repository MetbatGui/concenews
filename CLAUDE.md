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
| verify   | ✅      | 테스트 통과, 검증 완료         |

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

## 설계 원칙

모든 설계는 다음 원칙을 참고:

- **[DDD (Domain-Driven Design)](docs/architecture/principles/ddd.md)** — 4계층 구조, Repository 패턴
- **[XP (Extreme Programming)](docs/architecture/principles/xp.md)** — TDD, Refactoring, Simple Design
- **[Vertical Slices](docs/architecture/principles/vertical-slices.md)** — Spike → Spec → Plan → Integration Test → TDD

### Git & GitHub

- **[Git Workflow](docs/git-workflow.md)** — Branch strategy, Spike handling, Commit convention
- **[GitHub Strategy](docs/github-strategy.md)** — Milestones (Slice unit), Epic Issues, Labels, PR automation

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
