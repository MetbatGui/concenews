# Spike Process

> 불확실성 제거를 위한 로컬 학습 단계
> 기획 (Spec) 전에 기술 검증

---

## 정의

**Spike** = 임시 학습 코드 (commit X, 삭제 O)

목표:
- 기술적 불확실성 제거
- 데이터 구조/API 응답 검증
- 구현 전략 결정

---

## 라이프사이클

```
1. 불확실성 식별
   (예: "어떤 뉴스 API 쓸까?")

2. Spike 작성
   spikes/{topic}/ 생성
   임시 코드 작성

3. 실행 & 학습
   실제로 동작하는지 확인
   응답 구조, 제약사항 파악

4. LEARNINGS.md 기록
   발견사항, 결정, 이유 문서화

5. 삭제
   spikes/{topic}/ 완전 삭제 (LEARNINGS는 최상단에 유지)

6. 결정 반영
   Spec/Plan에 최종 결정 기록
```

---

## 규칙

### DO ✅

```
spikes/
  └─ {topic}/
     ├─ {source1}_spike.py
     ├─ {source2}_spike.py
     ├─ {source3}_spike.py
     └─ LEARNINGS.md

예:
spikes/
  └─ news_spikes/
     ├─ newsapi_spike.py
     ├─ reuters_rss_spike.py
     ├─ alpha_vantage_spike.py
     └─ LEARNINGS.md
```

- 로컬 폴더만 (git commit X)
- 임시 코드 (production quality 불필요)
- 명확한 목적 (무엇을 검증하나?)
- 학습 결과 기록 (LEARNINGS.md)

### DON'T ❌

```
spikes/
  ├─ newsapi_branch  (브랜치 쓰지 말 것)
  ├─ newsapi.py (주제 폴더 없음)
  └─ 결과 기록 안 함
```

- 브랜치 생성 (로컬 폴더만)
- commit 하기
- 결과 문서화 안 하기

---

## 예시: 뉴스 API 선택 Spike

### 1단계: 폴더 생성

```bash
mkdir -p spikes/news_spikes
```

### 2단계: 각 소스별 Spike 작성

**newsapi_spike.py**
```python
"""NewsAPI 평가 Spike."""
import requests

def test_newsapi():
    """NewsAPI 응답 구조 확인."""
    api_key = "YOUR_KEY"
    response = requests.get(
        "https://newsapi.org/v2/everything",
        params={"q": "interest rate", "apiKey": api_key}
    )
    
    data = response.json()
    if data.get("articles"):
        article = data["articles"][0]
        print("✓ 응답 구조:")
        print(f"  - title: {article.get('title')[:50]}")
        print(f"  - source: {article.get('source', {}).get('name')}")
        print(f"  - publishedAt: {article.get('publishedAt')}")

if __name__ == "__main__":
    test_newsapi()
```

**reuters_rss_spike.py**
```python
"""Reuters RSS 평가 Spike."""
import feedparser

def test_reuters_rss():
    """Reuters RSS 응답 구조 확인."""
    feed_url = "https://feeds.reuters.com/finance/markets"
    feed = feedparser.parse(feed_url)
    
    print(f"✓ 피드 제목: {feed.feed.title}")
    print(f"✓ 항목 개수: {len(feed.entries)}")
    
    if feed.entries:
        entry = feed.entries[0]
        print("✓ 항목 구조:")
        print(f"  - title: {entry.get('title', '')[:50]}")
        print(f"  - link: {entry.get('link', '')}")
        print(f"  - published: {entry.get('published', '')}")

if __name__ == "__main__":
    test_reuters_rss()
```

### 3단계: 실행 & 학습

```bash
cd spikes/news_spikes
python newsapi_spike.py
python reuters_rss_spike.py
```

결과:
```
✓ NewsAPI:
  - 응답: JSON, 명확한 구조
  - Rate: 100req/day
  - 설정: API Key 필수

✓ Reuters RSS:
  - 응답: XML 피드, 간결
  - Rate: 무제한
  - 설정: URL만 필요
```

### 4단계: LEARNINGS.md 작성

```markdown
# News Source Spike: Learnings & Decision

## Question
어떤 뉴스 소스를 사용할 것인가?

## Candidates Tested
1. NewsAPI.org
2. Reuters RSS
3. Alpha Vantage News

## Findings

### NewsAPI
- 응답: JSON
- Rate: 100 req/day (프리티어)
- 설정: API Key
- 금융 뉴스: 다양 (Reuters, Bloomberg 포함)

### Reuters RSS
- 응답: XML 피드
- Rate: 무제한
- 설정: URL만
- 금융 뉴스: 최강 (금융 전문)

### Alpha Vantage
- 응답: JSON/CSV
- Rate: 500 req/day (프리)
- 설정: API Key
- 금융 뉴스: 좋음 (경제 지표)

## Decision: Reuters RSS

### Why
- 무제한 요청 (API Key 불필요)
- 금융 뉴스 전문
- XML 피드 파싱 간단

### Implementation Note
- feedparser 라이브러리 사용
- 각 항목 → NewsItem 변환 (URL 해시로 ID)
```

### 5단계: Spike 폴더 삭제

```bash
rm -rf spikes/news_spikes/newsapi_spike.py
rm -rf spikes/news_spikes/reuters_rss_spike.py
rm -rf spikes/news_spikes/alpha_vantage_spike.py
# LEARNINGS.md는 유지
```

### 6단계: Spec 업데이트

Spec에 기록:
```
## 기술 결정

- **데이터 소스**: Reuters RSS
  - 참고: spikes/news_spikes/LEARNINGS.md
```

---

## LEARNINGS.md 템플릿

```markdown
# {Topic} Spike: Learnings & Decision

## Question
[무엇을 검증하나?]

## Candidates Evaluated
- Option 1
- Option 2
- Option 3

## Findings

### Option 1
- [특징]
- [제약]

### Option 2
- [특징]
- [제약]

## Decision: {선택지}

### Why
- [이유 1]
- [이유 2]

### Implementation Notes
- [구현 시 고려사항]
- [의존성]
```

---

## 체크리스트

Spike 완료 전:

- [ ] 각 후보 테스트 완료
- [ ] LEARNINGS.md 작성 (발견, 결정, 이유)
- [ ] 최종 선택 명확
- [ ] Spike 코드 삭제 (LEARNINGS는 유지)
- [ ] Spec/Plan에 결정 반영
