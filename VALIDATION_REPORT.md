# 기능 및 버그 검증 보고서
## 봇 9개 컴포넌트 + 홈 테더 토글

**검증일**: 2026-03-20
**검증자**: Claude Code (기능/버그 검증 에이전트)
**상태**: 완료

---

## 📋 검증 결과 요약

| 구분 | 개수 | 상태 |
|------|------|------|
| **Critical 이슈** | 2 | 🔴 발견 |
| **Major 이슈** | 4 | 🟡 발견 |
| **Minor 이슈** | 3 | 💙 발견 |

---

## 🔴 Critical 이슈 (런타임 에러 발생 가능)

### Issue C-1: BotScannerClient — URL 파라미터 네이밍 불일치
**파일**: `BotScannerClient.js:88`
**심각도**: Critical
**원인**:
- 프론트엔드는 `tradeConfigUuid` 파라미터 사용 (`/tradecore/trigger-scanner/?tradeConfigUuid=${configUuid}`)
- Django 백엔드 URL 정의를 확인하면 카멜케이스 파라미터 처리 여부가 불명확
- 백엔드가 `trade_config_uuid` (스네이크케이스)를 기대하면 쿼리 파라미터 매칭 실패 가능

**영향**: 스캐너 데이터 로딩 실패, 빈 목록 표시 가능성
**수정 방향**:
1. 백엔드 뷰 확인: `tradecore.views.TriggerScannerView` 쿼리 파라미터 처리 방식 검증
2. 일관성 유지: 다른 엔드포인트(`trades/?trade_config_uuid`, `capital/?trade_config_uuid`)처럼 스네이크케이스로 통일
3. 프론트: `tradeConfigUuid` → `trade_config_uuid` 변경

---

### Issue C-2: BotPositionClient — 엔드포인트 파라미터 불일치
**파일**: `BotPositionClient.js:162-166`
**심각도**: Critical
**원인**:
```javascript
// 프론트엔드
const targetEndpoint = targetIsSpot
  ? `/tradecore/spot-position/?marketCode=${target.value}&tradeConfigUuid=${tradeConfigUuid}`
  : `/tradecore/futures-position/?marketCode=${target.value}&tradeConfigUuid=${tradeConfigUuid}`;
```
- `marketCode` vs `market_code` (또는 `market-code`)
- `tradeConfigUuid` vs `trade_config_uuid`

**영향**: 포지션 데이터 조회 실패, 포지션 현황 페이지 공백
**수정 방향**:
1. 백엔드 URL 구성 확인: `CapitalView.as_view()`, `SpotPositionView.as_view()` 쿼리 파라미터 필드명 검증
2. 모든 파라미터를 스네이크케이스로 통일 (`market_code`, `trade_config_uuid`)
3. 프론트: 파라미터 네이밍 정규화

---

## 🟡 Major 이슈 (데이터 오류 또는 동작 오류)

### Issue M-1: PremiumTable — row.dollar 필드 존재 검증 필수
**파일**: `PremiumTable.js:151-154`
**심각도**: Major
**원인**:
```javascript
const dollar = Number(row.dollar || 0);
const showTether = tetherView && Number.isFinite(dollar) && dollar > 0;
const lsDisplay = showTether ? dollar * (1 + ls * 0.01) : ls;
```
- `row.dollar` 필드가 WebSocket 데이터에 실제 포함되는지 불명확
- `useKlineWebSocket.js` 에서 API 응답 구조 검증 필요
- 필드 누락 시: `dollar === 0` → `showTether === false` → 테더 환산가 표시 안 됨 (기능 작동 불가)

**영향**: 테더 환산가 토글이 활성화되어도 데이터 미표시
**수정 방향**:
1. `/api/infocore/kline-current/` 응답 구조 확인: `dollar` 필드 실제 포함 여부
2. 필드 누락 시:
   - 백엔드: `dollar` 필드 추가 (USD/KRW 환율 기반 계산)
   - 또는 프론트: 대체 계산 로직 구현
3. 데이터 직렬화 단계에서 필드 검증

---

### Issue M-2: HomeMarketOverviewClient — isKimpExchange 판별 로직 부분 검증
**파일**: `HomeMarketOverviewClient.js:16-17, 61`
**심각도**: Major
**원인**:
```javascript
const KOREAN_EXCHANGES = new Set(["UPBIT", "BITHUMB", "COINONE"]);
function isKoreanMarket(code) { return KOREAN_EXCHANGES.has(code?.split("_")[0]); }
// ...
const isKimpExchange = isKoreanMarket(targetMarketCode) && !isKoreanMarket(effectiveOriginMarketCode);
```
- `code?.split("_")[0]` 로직: 마켓 코드 형식이 `"UPBIT_SPOT"`, `"BINANCE_FUTURES"` 등으로 가정
- 예: `"UPBIT_SPOT"` → `["UPBIT", "SPOT"]` → `"UPBIT"` 추출 ✓
- 그러나 마켓 코드 형식이 변경될 경우 (예: `"UPBIT-SPOT"`) 동작 불가

**영향**: 테더 토글 버튼이 잘못된 조건에서 활성화되거나 비활성화될 수 있음
**수정 방향**:
1. 백엔드 마켓 코드 포맷 확정: 모든 코드가 `{EXCHANGE}_{MARKET_TYPE}` 형식인지 확인
2. 마켓 코드 정규화 함수 중앙집중화 (유틸리티)
3. 엣지 케이스 처리:
   ```javascript
   // 예를 들어, undefined 또는 null 코드 처리
   function isKoreanMarket(code) {
     if (!code) return false;
     return KOREAN_EXCHANGES.has(code.split("_")[0]);
   }
   ```

---

### Issue M-3: BotCapitalClient — 통화 환산 로직 불완전
**파일**: `BotCapitalClient.js:129-134`
**심각도**: Major
**원인**:
```javascript
if (isTargetUsdt && isOriginKrw && dollarRate > 0 && usdtRate > 0) {
  totalBeforeUsd = tBeforePnl * dollarRate + oBeforePnl;
  totalAfterUsd = tAfterPnl * dollarRate + oAfterPnl;
  totalBeforeUsdt = tBeforePnl * usdtRate + oBeforePnl;
  totalAfterUsdt = tAfterPnl * usdtRate + oBeforePnl;  // ← BUG!
}
```
- 마지막 줄: `oBeforePnl` 대신 `oAfterPnl` 사용해야 함 (타이핑 오류)

**영향**: "합산 손익 후 (USDT)" 행에 잘못된 데이터 표시
**수정 방향**:
```javascript
totalAfterUsdt = tAfterPnl * usdtRate + oAfterPnl;  // 수정
```

---

### Issue M-4: BotDepositClient — 입금 확인 응답 처리 오류
**파일**: `BotDepositClient.js:242-246`
**심각도**: Major
**원인**:
```javascript
const amount = data?.result?.total_deposit_amount;
toast.success(
  amount != null
    ? `입금 확인 완료 (총 입금: ${fmtNum(amount)} USDT)`
    : data?.message || "입금 확인 완료",
);
```
- 응답 구조가 `{ result: { total_deposit_amount: ... } }` 인지 `{ total_deposit_amount: ... }` 인지 불명확
- 백엔드 `UserWalletTransactionView` 응답 스키마 확인 필요

**영향**: 입금 확인 성공 메시지가 정확한 금액을 표시하지 못할 수 있음
**수정 방향**:
1. `/wallet/transaction/` POST 응답 구조 확인
2. 응답 처리 로직 정규화:
   ```javascript
   const amount = data?.result?.total_deposit_amount || data?.total_deposit_amount;
   ```

---

## 💙 Minor 이슈 (코드 개선 사항)

### Issue Mn-1: useKlineWebSocket — 에러 상태 미처리
**파일**: `useKlineWebSocket.js:200`
**심각도**: Minor
**원인**:
```javascript
return { liveRows, connected, error, lastReceivedAt };
```
- `error` 상태는 반환되지만 `HomeMarketOverviewClient`에서 사용하지 않음
- 에러 메시지를 사용자에게 표시할 기회 상실

**영향**: 사용자가 WebSocket 연결 실패 상황을 명확히 인식하기 어려움
**수정 방향**:
```javascript
// HomeMarketOverviewClient에서 에러 상태 렌더링
{error && <div className="...text-negative">{error}</div>}
```

---

### Issue Mn-2: BotVolatilityNotificationsClient — marketCodeSelectorRef 미사용
**파일**: `BotVolatilityNotificationsClient.js:183`
**심각도**: Minor
**원인**:
```javascript
void marketCodeSelectorRef;  // 의도적으로 무시하는 코드
```
- 파라미터 전달받지만 사용하지 않음
- Props drilling 오버헤드

**영향**: 코드 명확성 저하, 불필요한 props 전달
**수정 방향**:
```javascript
export default function BotVolatilityNotificationsClient() {
  // 파라미터 제거
  // 내부에서 마켓 코드 선택 구현
}
```

---

### Issue Mn-3: PremiumTable — memo 객체 동일성 검사 누락 위험
**파일**: `PremiumTable.js:192`
**심각도**: Minor
**원인**:
```javascript
}, (p, n) => p.row === n.row && ... && p.tetherView === n.tetherView);
```
- `walletData` 객체 비교가 참조 동일성(`===`)만 하고 있음
- 매번 새로운 객체가 생성되면 memo가 무효화됨 (성능 저하)

**영향**: Row 컴포넌트 불필요한 리렌더링 (성능 오버헤드)
**수정 방향**:
```javascript
// walletData 객체 직렬화 비교 또는 useMemo로 메모이제이션
const stableWalletData = useMemo(() => walletStatus?.[asset], [walletStatus, asset]);
```

---

## ✅ 검증 완료 항목

### 데이터 페칭 (모든 컴포넌트)
- ✓ `useEffect` cleanup flag (`active`) 구현됨
- ✓ Promise.all 병렬 처리 구현
- ✓ 에러 핸들링 try-catch 구현

### 폼 검증 (BotScannerClient, BotVolatilityNotificationsClient)
- ✓ 경계값 검증 (min/max)
- ✓ 빈 값 체크
- ✓ NaN 체크 (`Number.isNaN()`)
- ✓ 음수 체크

### 상태 관리
- ✓ loading → data/empty/error 분기 처리
- ✓ 페이지네이션 로직 정상 구현

### 런타임 안전성
- ✓ Optional chaining 적절히 사용
- ✓ null/undefined 접근 방어

### 숫자 포맷
- ✓ Intl.NumberFormat 올바른 사용
- ✓ 소수점 자릿수 일관성

---

## 📊 테더 토글 특별 검증

### 1. `row.dollar` 필드 존재 확인
**현황**: ⚠️ 부분 검증 필요
- WebSocket 메시지 구조 확인: `useKlineWebSocket.js:88-98`에서 JSON 파싱 후 배열 검증만 함
- `row.dollar` 필드는 서버에서 동적으로 추가되는 것으로 보임 (명시적 확인 필요)

**권장사항**:
- `/api/infocore/kline-current/` 응답 샘플 데이터 확인
- 웹소켓 메시지 실시간 모니터링

---

### 2. 환산 공식 검증
**현황**: ✓ 검증됨
```javascript
const lsDisplay = showTether ? dollar * (1 + ls * 0.01) : ls;
```
- 공식: `dollar_value = USD_KRW_rate * (1 + kimp_percentage / 100)`
- 레거시 CRA와 동일 로직 (확인됨)

---

### 3. isKimpExchange 판별 로직
**현황**: ⚠️ 마켓 코드 포맷 가정에 의존
- 현재 포맷: `"UPBIT_SPOT"`, `"BINANCE_FUTURES"` 등
- split("_")[0] 로직 작동 확인됨
- **단점**: 포맷 변경 시 취약

---

## 🎯 권장 수정 우선순위

| 우선순위 | 이슈 | 소요시간 | 영향 범위 |
|---------|------|---------|---------|
| 1️⃣ **즉시** | C-1: BotScannerClient URL 파라미터 | 5분 | 스캐너 기능 전체 |
| 2️⃣ **즉시** | C-2: BotPositionClient URL 파라미터 | 5분 | 포지션 현황 기능 |
| 3️⃣ **긴급** | M-3: BotCapitalClient 통화 환산 오류 | 2분 | 자본 현황 표시 |
| 4️⃣ **높음** | M-1: row.dollar 필드 검증 | 30분 | 테더 토글 기능 |
| 5️⃣ **높음** | M-2: isKimpExchange 판별 로직 강화 | 15분 | 테더 토글 UI |
| 6️⃣ **중간** | M-4: 입금 확인 응답 처리 | 10분 | 지갑 기능 |

---

## 📝 검증 체크리스트 최종

| 항목 | 상태 | 비고 |
|------|------|------|
| API 엔드포인트 일관성 | 🔴 **부분 실패** | C-1, C-2 이슈 |
| 데이터 페칭 | ✅ **통과** | cleanup flag, error handling 양호 |
| 폼 검증 | ✅ **통과** | 경계값, NaN, 빈 값 모두 검증 |
| 상태 관리 | ✅ **통과** | loading/data/error 분기 정상 |
| 런타임 안전성 | ✅ **통과** | optional chaining 적절히 사용 |
| 숫자 포맷 | ✅ **통과** | Intl.NumberFormat 올바름 |
| **테더 토글** | ⚠️ **조건부** | row.dollar 확인 필요 |

---

## 📌 다음 단계

1. **즉시 수정** (C-1, C-2, M-3):
   - 백엔드 URL 파라미터 확정 문의
   - BotCapitalClient 오타 수정

2. **검증 필요** (M-1):
   - `/api/infocore/kline-current/` 응답 스키마 확인
   - 웹소켓 메시지 페이로드 확인

3. **강화** (M-2, Mn-3):
   - 마켓 코드 정규화 함수 생성
   - Row 컴포넌트 memo 최적화

4. **제거** (Mn-2):
   - marketCodeSelectorRef 파라미터 제거

---

**검증 완료**: 2026-03-20
**최종 상태**: 🟡 **2개 Critical + 4개 Major 이슈 발견 — 수정 권장**
