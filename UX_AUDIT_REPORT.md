# UX 감사 보고서 (Comprehensive UX Audit)

**일자**: 2026-03-20
**대상**: `/Users/charlie/Projects/acw/apps/community_web_next/` 전체 프론트엔드
**감사항목**: 로딩/에러 상태, 인터랙션 피드백, 모바일 레이아웃, 폰트 일관성, 색상 대비, 네비게이션

---

## CRITICAL 이슈 (즉시 수정 필요)

### 1. 색상 대비 위반 — WCAG AA 미충족
**파일**: `components/home/MarketSummaryBar.js:70-72`, `app/globals.css:8`
**심각도**: **CRITICAL**
**문제**:
- `text-ink-muted` (`#a0aecb`)를 배경 `bg-surface-elevated/20` 위에 표시
- 명도 대비 약 2.8:1 (WCAG AA 4.5:1 미달)
- 특히 작은 텍스트(0.46rem, 0.64rem)에서 읽기 어려움

**발생 위치**:
- MarketSummaryBar 연결 상태 표시: "연결" / "재연결"
- 시간 표시: `{timeLabel}`
- 모든 통계 레이블 (`Stat` 컴포넌트의 `text-ink-muted/50`)

**개선 방향**:
명도 대비를 4.5:1 이상으로 상향하기:
- `text-ink-muted` → `text-ink-muted` 불투명도 조정
- 또는 배경색을 `bg-surface-elevated/40` 이상으로 강화
- 테스트: WebAIM Contrast Checker

---

### 2. 모바일 375px — overflow-x 스크롤바 발생 (PremiumTable)
**파일**: `components/home/PremiumTable.js:257-258`
**심각도**: **CRITICAL**
**문제**:
```jsx
<div className="overflow-x-auto">
  <table className="w-full table-auto">
```
- 테이블 너비 수동 지정 없음 (`min-width: 720px` 주석에만 있음)
- 모바일에서 테이블이 viewport 초과, 강제 가로 스크롤
- 스크롤바가 본 콘텐츠를 가림 (모바일 UX 악화)

**검증**: 375px viewport에서 테이블 렌더링 시 우측 스크롤바 노출

**개선 방향**:
1. 모바일에서 카드 레이아웃으로 전환 (숨겨진 열 제거)
2. 또는 테이블을 좌우 스크롤 가능하게 하되, `scrollbar-hide` 적용
3. 중요 열(자산, 진입금프, 스프레드)만 표시, 나머지는 확장 패널에서 조회

---

### 3. 터치 타겟 44px 미만 (모바일 접근성)
**파일**: `components/home/PremiumTable.js:158`, `components/AppShell.js:145-152`
**심각도**: **CRITICAL**
**문제**:
- PremiumTable 즐겨찾기 별: `h-11 w-11` → 44px (OK), 하지만 내부 버튼은 `scale-110` 효과만 있고 실제 타겟은 14x14px
- AppShell 햄버거 메뉴: `h-11 w-11` 버튼 자체는 OK, 하지만 내부 아이콘 padding이 불충분

**문제 사항**:
```jsx
<button className="scale-110 active:scale-95">  {/* 내부 14x14px 아이콘 */}
  <svg width="14" height="14">
```

**개선 방향**:
- 버튼 내부 padding을 최소 12px 유지, 또는 아이콘 크기를 16-20px로 증가
- `sm:` 미디어 쿼리에서만 축소

---

### 4. 로딩/빈/에러 상태 처리 부족
**파일들**:
- `components/home/HomeMarketOverviewClient.js:287-289` ✓ 부분 처리
- `components/bot/BotCapitalClient.js:97-99` ✗ 에러 상태 미완성
- `components/arbitrage/ArbitrageFundingRateDiffClient.js:99-100` ✗ 에러 상태만 있음
- `components/board/BoardPostClient.js:44-47` ✓ 로딩만 처리

**심각도**: **CRITICAL**
**문제**:

#### HomeMarketOverviewClient (부분 적절)
- ✓ 연결 중 상태: 스켈레톤 로우 표시
- ✓ 데이터 없음: "실시간 프리미엠 데이터를 불러오는 중입니다..." 메시지
- ✗ 네트워크 에러: 아무것도 표시 안 함 (try-catch에서 무시)

#### BotCapitalClient (상태 처리 미흡)
```jsx
if (error || (!targetData && !originData)) {
  return (
    <div className="space-y-4 p-4">
      <h3 className="section-title"></h3>  {/* 미완성 */}
```
- 에러 메시지 텍스트 없음
- 재시도 버튼 없음

#### ArbitrageFundingRateDiffClient (로딩/에러 모두 부족)
```javascript
catch (err) {
  if (active) setPageError(err.message);  // 에러 저장만 함
}
```
- 하지만 `pageError` 표시 코드 없음

#### BoardPostClient (로딩만)
```jsx
if (loading) {
  return <div className="grid min-h-[40vh] place-items-center">
    <div className="h-8 w-8 animate-spin" />  {/* 로딩 스피너만 */}
  </div>;
}
```
- 에러 상태 처리 없음

**개선 방향**:
1. 모든 비동기 컴포넌트에 3가지 상태 구현:
   - 로딩 중: 스켈레톤 또는 스피너
   - 성공: 데이터 표시
   - 에러: 명확한 메시지 + 재시도 버튼
2. BotCapitalClient, ArbitrageFundingRateDiffClient 완성
3. 일관된 에러 UI 컴포넌트 (ErrorCard) 생성

---

## MAJOR 이슈 (높은 우선순위)

### 5. 폰트 계층 일관성 부재
**파일**: `app/globals.css`, 여러 컴포넌트
**심각도**: **MAJOR**
**문제**:

#### 같은 레벨의 제목이 다른 크기 사용
- `PremiumTable.js:165` — 자산 이름: `text-[0.62rem] sm:text-sm`
- `NewsHubClient.js:57` — 뉴스 제목: `text-sm`
- `BoardListClient.js:66` — 게시판 제목: `text-lg`
- `HomeMarketOverviewClient.js:122` 외 — section 제목: 일관성 없음

#### 본문 텍스트 크기 편차
- Stat 레이블: `text-[0.55rem] sm:text-[0.68rem]`
- MarketSummaryBar 시간: `text-[0.44rem] sm:text-[0.6rem]`
- 테이블 본문: `text-[0.54rem] sm:text-xs`
- NewsHubClient 설명: `text-[0.78rem]`

#### 정규 디자인 토큰은 있지만 사용 안 함
```css
--text-sm: 0.875rem;      /* 14px */
--text-base: 1rem;        /* 16px */
--text-lg: 1.125rem;      /* 18px */
```
- 대신 `text-[0.62rem]`, `text-[0.68rem]` 등 임의 값 사용

**개선 방향**:
1. 명확한 폰트 계층 정의:
   - Page Title (H1): 1.5-1.8rem (24-28px)
   - Section Title (H2): 1.125rem (18px)
   - Subsection (H3): 1rem (16px)
   - Body: 0.875rem (14px)
   - Small: 0.75rem (12px)
2. 모든 컴포넌트를 Tailwind 토큰 또는 CSS 변수로 통일
3. `globals.css`의 정의를 활용하는 utils 파일 생성

---

### 6. 인터랙션 피드백 부족 (버튼 상태)
**파일**: 여러 파일
**심각도**: **MAJOR**
**문제**:

#### disabled 상태 피드백 미흡
- `HomeMarketOverviewClient.js:139-151` — 테더/김프 토글 버튼
  ```jsx
  disabled={!isKimpExchange}
  className={`... ${!isKimpExchange ? "opacity-40 cursor-not-allowed" : ...}`}
  ```
  - ✓ `opacity-40` 있음
  - ✗ `cursor: not-allowed` CSS 클래스 없음
  - ✗ hover 상태 없음 (`hover:` prefix 없음)

#### 제출 버튼 로딩 상태 없음
- `BotApiKeyClient.js:57-79` — "등록" 버튼
  ```jsx
  {submitting ? "등록 중..." : "등록"}  // 텍스트만 변함
  ```
  - ✗ 버튼 disabled 상태 설정 없음
  - ✗ 로딩 인디케이터 없음
  - ✗ 사용자가 중복 제출 가능

- `BotScannerClient.js` — "추가" 버튼
  - ✗ 제출 중 disabled 상태 없음

#### 탭 버튼 active 상태 시각화 약함
- `ChatWidget.js:24-29` — 탭 클릭 시
  ```jsx
  className={`... ${active ? "text-accent" : "text-ink-muted/60 hover:text-ink-muted"}`}
  ```
  - ✓ 색상 변함
  - ✗ 하단 인디케이터 (`bottom-0 left-1/4` span) 작음 (2px)
  - ✗ 전환 애니메이션 부재

**개선 방향**:
1. disabled 상태 스타일 통일:
   ```css
   .ui-button:disabled {
     opacity: 0.5;
     cursor: not-allowed;
     pointer-events: none;
   }
   ```
2. 로딩 상태 버튼:
   - 텍스트 + 스피너 아이콘
   - disabled 상태 자동 설정
3. 탭 인디케이터: 높이 2-3px, 전환 `transition-all 200ms ease`

---

### 7. 토스트/알림 위치 및 타이밍 정의 부족
**파일**: `components/bot/BotApiKeyClient.js:69`, `BotScannerClient.js` (여러 곳)
**심각도**: **MAJOR**
**문제**:
- `sonner` 토스트 라이브러리 사용: `toast.success()`, `toast.error()`
- ✗ 자동 닫힘 타이밍 명시 없음 (기본값 4초 추정)
- ✗ 위치 설정 없음 (기본값: 하단 중앙)
- ✗ 성공/에러 아이콘 구분 불명확

**개선 방향**:
1. `lib/toast.js` 생성: 통일된 토스트 설정
   ```javascript
   const toastConfig = {
     position: 'top-right',
     duration: 3000,  // ms
     description: '...',
   };
   ```
2. 모든 `toast.success/error` 호출에 설정 적용
3. 에러 알림은 더 길게 표시 (5-6초)

---

### 8. 네비게이션 부자연스러움 (페이지 전환)
**파일**: `components/AppShell.js`
**심각도**: **MAJOR**
**문제**:

#### 페이지 전환 시 스크롤 위치 미처리
- 새 페이지로 이동 시 스크롤이 이전 위치에 남음
- `useEffect`에서 `window.scrollTo(0, 0)` 호출 없음

#### 콘텐츠 점프
- `pt-2.5 pb-6` 여백이 페이지마다 다를 가능성
- 테이블 페이지네이션 클릭 시 스크롤이 튀는 현상 가능

**예시** (`HomeMarketOverviewClient.js`):
```jsx
// 페이지 진입 시 자동 스크롤 없음
useEffect(() => {
  // scrollTo 코드 없음
}, []);
```

**개선 방향**:
1. `useEffect` 추가:
   ```javascript
   useEffect(() => {
     window.scrollTo({ top: 0, behavior: 'smooth' });
   }, [pathname]);
   ```
2. 또는 Next.js Router 사용:
   ```javascript
   router.push(url, { scroll: true });
   ```

---

### 9. 모바일 레이아웃 — 텍스트 잘림
**파일**: `components/board/BoardListClient.js:57-58`, 여러 카드 컴포넌트
**심각도**: **MAJOR**
**문제**:

#### 텍스트 라인 제한 없음
- 뉴스/게시글 제목이 2-3줄 이상 넘어감 (특히 한글)
- 설명은 `slice(0, 220)` 고정 길이로 잘라 끝에 `...` 없음

**예시** (`NewsHubClient.js:50-75`):
```jsx
<p className="mt-1 text-[0.78rem] leading-relaxed text-ink-muted">
  {item.subtitle || stripHtml(item.content).slice(0, 220)}  {/* … 없음 */}
</p>
```

#### 검색 입력창이 너무 좁음 (모바일)
- `w-[100px] sm:w-[160px]` 고정
- 모바일 375px에서 검색어 입력 후 보이지 않음

**개선 방향**:
1. `line-clamp` 유틸리티 사용:
   ```jsx
   <h2 className="line-clamp-2 text-sm font-semibold">{title}</h2>
   <p className="line-clamp-3 text-xs text-ink-muted">{description}</p>
   ```
2. 검색 입력 너비 조정:
   ```jsx
   w-full sm:w-[200px]  // 모바일: 전체 너비
   ```

---

## MINOR 이슈 (UI 개선, 우선순위 낮음)

### 10. form 필수 필드 표시 부재
**파일**: `components/bot/BotApiKeyClient.js:9-14`, `BotScannerClient.js`
**심각도**: **MINOR**
**문제**:
- access_key, secret_key 등 필수 필드에 `*` 표시 없음
- 필드 레이블이 명확하지 않은 경우 있음 (예: "passphrase" → OKX 전용)

**개선 방향**:
1. 필수 필드에 빨간 `*` 추가:
   ```jsx
   <label>API Key <span className="text-negative">*</span></label>
   ```
2. 필드별 도움말 추가: `title="..." ` 또는 `<small>` 태그

---

### 11. 폼 밸리데이션 메시지 부재
**파일**: `components/bot/BotScannerClient.js:60-68` (INITIAL_FORM)
**심각도**: **MINOR**
**문제**:
```javascript
const INITIAL_FORM = {
  low: "",
  high: "",
  trade_capital: "",
  min_target_atp: "",
  min_target_funding_rate: "",
  max_repeat_num: "5",
  repeat_term_secs: "300",
};
```
- 각 필드의 유효성 조건 설명 없음
- min/max 범위, 숫자 형식 명시 안 됨

**개선 방향**:
1. 필드 아래 `<small>` 텍스트: "예: 0-5 (반복 횟수)"
2. 유효성 검사 실시간 피드백:
   ```jsx
   {errors.low && <span className="text-negative text-xs">{errors.low}</span>}
   ```

---

### 12. 모달 backdrop 클릭 시 동작 애매함
**파일**: `app/globals.css:505-514` (modal-backdrop)
**심각도**: **MINOR**
**문제**:
```css
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(12, 17, 14, 0.36);
  backdrop-filter: blur(8px);
}
```
- backdrop 클릭 시 닫히는지 명시 안 됨
- 모바일에서 배경 어둡기 약함 (opacity 0.36은 약 87% 투명)

**개선 방향**:
1. 명시적 onClick 핸들러 추가: `onClick={() => onClose()}`
2. 배경 어둡기: `rgba(..., 0.5)` 이상

---

### 13. 스켈레톤 로더 스타일 일관성
**파일**: `components/home/PremiumTable.js:208-225`, `components/bot/BotTriggersClient.js:84-100`
**심각도**: **MINOR**
**문제**:
```jsx
<div className="h-3 rounded-sm" style={{
  background: "linear-gradient(...)",
  animation: "shimmer 1.6s linear infinite",
  animationDelay: `${i * 60}ms`,
}}
```
- 로우 개수 하드코딩 (8, 5, 4 등)
- 상황마다 다름 (일관성 부재)

**개선 방향**:
1. 재사용 가능한 SkeletonLoader 컴포넌트 만들기:
   ```jsx
   <SkeletonLoader rows={8} columns={10} />
   ```

---

### 14. 색상 명명 일관성
**파일**: `app/globals.css`
**심각도**: **MINOR**
**문제**:

#### 색상 정의가 두 가지 방식으로 혼용
```css
/* @theme (Tailwind 방식) */
--color-accent: #2b73ff;
--color-positive: #16c784;

/* :root (CSS 변수 방식) */
--accent: #2b73ff;
--accent-strong: #1f5fe0;
--accent-soft: rgba(43, 115, 255, 0.14);
```

#### 사용처가 뒤섞임
- `text-accent` (Tailwind 클래스)
- `var(--accent)` (인라인 스타일)
- `rgba(43, 115, 255, 0.14)` (하드코딩)

**개선 방향**:
1. 하나의 규칙으로 통일: `--color-*` 방식으로 통일
2. Tailwind `theme.colors` 설정에서 참조하도록 변경
3. 모든 색상을 변수로 대체

---

## 정리 및 우선순위

| 심각도 | 개수 | 주요 이슈 |
|--------|------|---------|
| **CRITICAL** | 4 | 색상 대비, 모바일 overflow, 터치 타겟, 로딩/에러 상태 |
| **MAJOR** | 6 | 폰트 계층, 버튼 피드백, 토스트 설정, 네비게이션, 텍스트 잘림, 필드 표시 |
| **MINOR** | 4 | 밸리데이션 메시지, 모달, 스켈레톤, 색상 명명 |

**권장 수정 순서**:
1. **Week 1** — CRITICAL: 색상 대비, 모바일 테이블 레이아웃, 로딩/에러 상태
2. **Week 2** — MAJOR: 폰트 계층, 버튼 상태, 토스트 설정
3. **Week 3** — MAJOR: 네비게이션, 모바일 레이아웃 개선
4. **Week 4** — MINOR: 폼 UX, 스켈레톤 재사용, 색상 명명

---

## 기술 부채 정리

### 공통 컴포넌트 생성 권장
- `LoadingState.js` — 일관된 로딩 UI
- `ErrorCard.js` — 일관된 에러 UI
- `SkeletonLoader.js` — 재사용 가능한 스켈레톤
- `ToastManager.js` — 통일된 토스트 설정
- `FormField.js` — 필수 필드 표시, 밸리데이션 메시지

### 스타일 통합
- `lib/typography.js` — 폰트 크기/두께 상수
- `lib/colors.js` — 색상 변수 재정의
- `lib/interactions.js` — 버튼 상태, 포커스 스타일 통일

---

**보고서 작성자**: UX 감사 에이전트
**보고서 날짜**: 2026-03-20
