# Polymarket 시스템성 지갑 관측 자격 Spike

**실행일**: 2026-08-15

## 질문

Polymarket 상위 보유자 데이터에서 운영·정산·토큰 변환 성격의 지갑을 일반 참여자 관측 대상에서 안전하게 제외할 수 있는가?

## 대상

- 지갑: `0xa5ef39c3d3e10d0b270233af41cac69796b12966`
- 이벤트: 2026년 9월 FOMC 금리 결과의 다섯 이진 마켓

## 관찰

### Holder 응답 구조

- `GET /holders`의 응답은 outcome token별 그룹 배열이다.
- 각 그룹의 `holders` 배열을 펼쳐야 실제 상위 보유자를 비교할 수 있다.
- 2026년 8월 15일 기준, 대상 지갑은 다섯 마켓 모두에서 `No`(`outcomeIndex=1`) 1위였고, 각 보유량은 정확히 `3,105,640.982157` 지분이었다.

### 공개 활동과 포지션의 불일치

- Data API의 공개 활동은 `YIELD` 2건뿐이었다.
- `takerOnly=false`로 maker 체결을 포함해 조회한 공개 거래 이력은 0건이었다.
- 포지션 API에는 서로 배타적인 다수 이벤트 결과에 같은 대규모 잔고가 반복되고, 일부 포지션의 `totalBought`는 0으로 표시된다.

### 온체인·상품 구조 근거

- PolygonScan에서 이 지갑은 Polymarket Neg Risk Adapter 및 Neg Risk CTF Collateral Adapter로부터 대규모 ERC-1155 토큰을 반복 수령한다.
- Polymarket의 Neg Risk 구조에서는 한 결과의 `No` 토큰을 이벤트의 다른 결과 `Yes` 토큰들로 변환할 수 있다.
- 조건부 토큰은 거래소 체결 외에도 split, merge, conversion으로 생성·이동할 수 있다. 따라서 보유 잔고는 곧바로 방향성 거래 또는 일반 투자자의 자금 유입을 뜻하지 않는다.

## 결론

대상 지갑을 Polymarket 소유·운영 계정이라고 공개 데이터만으로 확정할 수는 없다. 그러나 공개 거래 근거 없이 Neg Risk Adapter 흐름에서 반복적으로 대규모 토큰을 수령하며, 상호 연관된 결과에 기계적으로 동일한 잔고를 갖는 것은 일반 참여자 신호로 해석할 수 없는 충분한 근거다.

후속 Slice의 정책은 **지갑 소유자를 추정하지 않고, 관측 자격을 판정**해야 한다.

1. 이 지갑은 감사 가능한 근거와 함께 초기 제외 목록에 넣는다.
2. 자동 제외는 지갑의 공개 거래 근거가 없고, 동일 이벤트의 Neg Risk 결과 전반에 기계적으로 반복되는 대규모 잔고가 확인될 때만 후보가 된다.
3. 자동 규칙만으로 즉시 영구 제외하지 않는다. 후보는 근거를 기록하고 사람이 제외 목록에 추가한다.
4. 원본 스냅샷은 보존하되, 상위 참여자·포지션 변화·대규모 자금 신호의 계산과 표시에서 제외한다.
5. UI와 문서에서 `운영 계정`, `마켓메이커`라고 단정하지 않고 `거래 참여자로 귀속할 수 없는 제외 지갑`으로 표현한다.

## 후속 구현에 필요한 계약

- 제외 목록은 지갑 주소, 제외 사유, 근거 URL, 등록일, 검토 상태를 보존한다.
- 스냅샷 수집은 원본 데이터를 모두 저장한 후 관측·신호 조회 단계에서 제외 목록을 적용한다.
- 목록 변경은 제품 신호의 의미를 바꾸므로 ADR과 검토 가능한 변경 이력이 필요하다.

## 참고

- [Polymarket Negative Risk Markets](https://docs.polymarket.com/advanced/neg-risk)
- [Polymarket Conditional Token Framework](https://docs.polymarket.com/trading/ctf/overview)
- [Polymarket 사용자 활동 API](https://docs.polymarket.com/api-reference/core/get-user-activity)
- [PolygonScan 대상 지갑 수령 거래 예시](https://polygonscan.com/tx/0xdfa24340b53b3b78bc589643f3f5c7b9e386b545a06ba349113a606decf3744c)
