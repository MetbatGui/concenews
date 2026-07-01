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
