# Macro vs Non-Macro Tag Classification

**데이터 출처**: GET /tags (2026-07-11)  
**목표**: Phase 1 market 필터링용

---

## MACRO_TAGS (화이트리스트 - 포함할 태그)

### 거시경제
| Tag ID | Label | Slug | 설명 |
|--------|-------|------|------|
| 933 | Federal Government | federal-government | 미 연방정부 정책 |
| 1396 | International Affairs | international-affairs | 국제 이슈 |
| 101026 | FDIC | fdic | 금융 규제 |
| 833 | ETF | etf | 자산 운용 |
| 101611 | Altcoins | altcoins | 암호화폐 |
| 537 | OpenAI | openai | AI 기술/정책 |
| 777 | Maritime Transport | maritime-transport | 해운 |
| 103482 | COP | cop | 환경 회담 (Conference of Parties) |
| 103357 | Influenza | influenza | 질병/보건 |
| 103269 | Korea | korea | 지정학 (한국/북한) |
| 101247 | Macro Graph | macro-graph | 거시 차트 |
| 101250 | Macro Single | macro-single | 단일 거시 이벤트 |

### 잠정 포함 (명확하지만 모호)
| Tag ID | Label | 설명 | 판단 |
|--------|-------|------|------|
| 100344 | House Races | 미국 하원 선거 | ✓ 거시경제 영향 |
| 104272 | Shenzhen | 중국 도시 | ⚠️ 지정학 (경제) |
| 100743 | Los Angeles | 미국 도시 | ⚠️ 지역 경제 뉴스 가능 |

---

## NON_MACRO_TAGS (블랙리스트 - 제외할 태그)

### 스포츠
| Tag ID | Label | Slug |
|--------|-------|------|
| 101025 | Viktoria Plzen | viktoria-plzen |
| 100626 | Europa League | europa-league |
| 103813 | Major League Cricket | major-league-cricket |
| 101104 | Stoke City | stoke-city |
| 102076 | QB | qb |

### 엔터테인먼트 & 인물
| Tag ID | Label | 설명 |
|--------|-------|------|
| 1512 | Caitlin Clark | NBA 선수 |
| 102136 | Timothée Chalamet | 배우 |
| 945 | Michelle Obama | 정치인 (인물) |
| 101561 | Alireza Firouzja | 체스 선수 |
| 100257 | Keith Gill | GameStop 투기꾼 |
| 101457 | Jerry After Dark | 엔터 |
| 104208 | Caesars Entertainment | 카지노/엔터 |
| 104393 | Vitality | e스포츠 팀 |

### 기타 (모호/불명확)
| Tag ID | Label | 설명 |
|--------|-------|------|
| 790 | Controversies | 논쟁 (정치?) |
| 1571 | Popularity | 인기도 |
| 330 | Season Finale | TV/엔터 |
| 101896 | Bat | ❓ 불명확 |
| 100601 | Virgins | ❓ 불명확 |
| 101655 | Wildfire | ❓ 자연재해? |
| 100881 | Russ | ❓ 인물? |
| 104377 | Yom | ❓ 불명확 |
| 713 | Tradition | ❓ 불명확 |
| 733 | Haniyeh | ❓ 인물? |
| 101091 | Kansas | ❓ 지역 뉴스? |
| 100735 | Philly | ❓ 지역 (필라델피아) |
| 103303 | Claude | ✓ AI (다목적, 중립) |
| 101247 | Macro Graph | ✓ MACRO로 분류 |
| 101250 | Macro Single | ✓ MACRO로 분류 |

### 불명확한 것들
- `product-market-fit` (101867): 비즈니스 개념 (exclude)
- `COP` (103482): Conference of Parties = 환경 회담 (include)
- `Influenza`: 질병 (건강정책 = include)

---

## Phase 1 필터링 규칙

```python
MACRO_TAG_IDS = [
  "933",      # federal-government
  "1396",     # international-affairs
  "1026",     # FDIC
  "833",      # ETF
  "101611",   # Altcoins
  "537",      # OpenAI
  "777",      # maritime-transport
  "103482",   # COP
  "103357",   # Influenza
  "103269",   # Korea
  "101247",   # Macro-Graph
  "101250",   # Macro-Single
  "100344",   # House-Races (선택사항)
]

NON_MACRO_TAG_IDS = [
  # 스포츠
  "101025", "100626", "103813", "101104", "102076",
  
  # 엔터 & 인물
  "1512", "102136", "945", "101561", "100257", "101457", "104208", "104393",
  
  # 모호
  "790", "1571", "330", "101896", "100601", "101655", "100881", "104377",
  "713", "733", "101091", "100735", "101867",
]

# 사용
macro_markets = set()
for tag_id in MACRO_TAG_IDS:
    markets = GET /markets?tag_id={tag_id}&limit=100
    macro_markets.update([m["id"] for m in markets])

for tag_id in NON_MACRO_TAG_IDS:
    non = GET /markets?tag_id={tag_id}&limit=100
    macro_markets -= {m["id"] for m in non}
```

---

## 문제점 & 다음 단계

1. **모호한 태그** (10개): 수동 검토 필요 (bat, virgins, wildfire, etc.)
2. **지역 태그**: Los Angeles, Kansas, Philly = 지역 경제 뉴스?
3. **인물 태그**: Michelle Obama = 정치? 엔터?

**해결책**: 
- Phase 1: MACRO_TAG_IDS만 사용 (conservative)
- Phase 2: LLM 분류로 보정
- Phase 3: 사용자 피드백 (trader annotation)

---

**작성**: 2026-07-11  
**상태**: 초안 (검증 필요)
