"use client";

import { Fragment, memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Star } from "lucide-react";

import PremiumChartPanel from "./PremiumChartPanel";
import ExchangeIcon from "../ui/ExchangeIcon";
import Tooltip from "../ui/Tooltip";

const PAGE_SIZE = 50;

// Responsive visibility classes per column
// mobile(<640): 자산, 현재가, 진입김프, 스프레드, 거래액 (5 cols)
// tablet(640-1024): + 즐겨찾기, 탈출김프 (7 cols)
// desktop(>1024): all 11 cols
const VIS = {
  fav: "hidden sm:table-cell",
  exit: "hidden sm:table-cell",
  lgOnly: "hidden md:table-cell",
};

function formatNumber(value, maximumFractionDigits = 2, minimumFractionDigits = 0) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits,
    minimumFractionDigits,
  }).format(Number(value));
}

function formatPercent(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return `${Number(value).toFixed(4)}%`;
}

function formatFundingPercent(value, digits = 3) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return `${Number(value).toFixed(digits)}%`;
}

function formatVolatility(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return Number(value).toFixed(2);
}

function formatKoreanVolume(value) {
  const numberValue = Number(value || 0);

  if (!Number.isFinite(numberValue)) {
    return "-";
  }

  if (Math.abs(numberValue) >= 1_0000_0000) {
    return `${(numberValue / 1_0000_0000).toFixed(1)}억`;
  }

  if (Math.abs(numberValue) >= 1_0000) {
    return `${(numberValue / 1_0000).toFixed(0)}만`;
  }

  return formatNumber(numberValue, 0, 0);
}

function polarityColor(value) {
  const n = Number(value || 0);
  if (n > 0) return "text-positive";
  if (n < 0) return "text-negative";
  return "text-ink-muted";
}

function premiumColorStyle(value, maxAbs = 3) {
  const n = Number(value || 0);

  if (n === 0) {
    return { color: "var(--color-ink-muted)" };
  }

  const abs = Math.abs(n);
  const t = Math.min(1, abs / maxAbs);

  if (n > 0) {
    const chroma = 0.06 + t * 0.16;
    return { color: `oklch(0.76 ${chroma.toFixed(3)} 155)` };
  }

  const chroma = 0.06 + t * 0.18;
  return { color: `oklch(0.68 ${chroma.toFixed(3)} 25)` };
}

function isSpotMarket(marketCode) {
  return marketCode?.toUpperCase()?.includes("_SPOT");
}

function extractExchange(marketCode) {
  return marketCode?.split("_")?.[0] || "";
}

function uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
}

function intersect(left, right) {
  const rightSet = new Set(right || []);
  return uniq((left || []).filter((item) => rightSet.has(item)));
}

function summarizeWalletStatus(walletStatus, targetMarketCode, originMarketCode, asset) {
  const assetStatus = walletStatus?.[asset];
  if (!assetStatus) {
    return {
      right: [],
      left: [],
      all: [],
    };
  }

  const targetExchange = extractExchange(targetMarketCode);
  const originExchange = extractExchange(originMarketCode);

  const targetWithdrawNetworks = assetStatus?.[targetExchange]?.withdraw || [];
  const targetDepositNetworks = assetStatus?.[targetExchange]?.deposit || [];
  const originWithdrawNetworks = assetStatus?.[originExchange]?.withdraw || [];
  const originDepositNetworks = assetStatus?.[originExchange]?.deposit || [];

  return {
    right: intersect(targetWithdrawNetworks, originDepositNetworks),
    left: intersect(targetDepositNetworks, originWithdrawNetworks),
    all: uniq([
      ...targetDepositNetworks,
      ...targetWithdrawNetworks,
      ...originWithdrawNetworks,
      ...originDepositNetworks,
    ]),
  };
}

function buildWalletStatusTooltip(summary, walletStatus, targetMarketCode, originMarketCode, asset) {
  const assetStatus = walletStatus?.[asset];
  if (!assetStatus) {
    return "지갑 상태 없음";
  }

  const targetExchange = extractExchange(targetMarketCode);
  const originExchange = extractExchange(originMarketCode);
  const targetLabel = targetExchange || "Target";
  const originLabel = originExchange || "Origin";

  const targetDeposit = assetStatus?.[targetExchange]?.deposit || [];
  const targetWithdraw = assetStatus?.[targetExchange]?.withdraw || [];
  const originDeposit = assetStatus?.[originExchange]?.deposit || [];
  const originWithdraw = assetStatus?.[originExchange]?.withdraw || [];

  if (isSpotMarket(targetMarketCode) && isSpotMarket(originMarketCode) && targetExchange !== originExchange) {
    return [
      `${targetLabel}→${originLabel}: ${summary.right.length ? summary.right.join(", ") : "-"}`,
      `${targetLabel}←${originLabel}: ${summary.left.length ? summary.left.join(", ") : "-"}`,
      `${targetLabel} 출금: ${targetWithdraw.length ? targetWithdraw.join(", ") : "-"}`,
      `${originLabel} 입금: ${originDeposit.length ? originDeposit.join(", ") : "-"}`,
      `${targetLabel} 입금: ${targetDeposit.length ? targetDeposit.join(", ") : "-"}`,
      `${originLabel} 출금: ${originWithdraw.length ? originWithdraw.join(", ") : "-"}`,
    ].join(" | ");
  }

  return [
    `${targetLabel} 입금: ${targetDeposit.length ? targetDeposit.join(", ") : "-"}`,
    `${targetLabel} 출금: ${targetWithdraw.length ? targetWithdraw.join(", ") : "-"}`,
    `${originLabel} 입금: ${originDeposit.length ? originDeposit.join(", ") : "-"}`,
    `${originLabel} 출금: ${originWithdraw.length ? originWithdraw.join(", ") : "-"}`,
  ].join(" | ");
}

function WalletStatusCell({ summary, tooltipText, targetMarketCode, originMarketCode }) {
  const bothSpot =
    isSpotMarket(targetMarketCode) &&
    isSpotMarket(originMarketCode) &&
    extractExchange(targetMarketCode) !== extractExchange(originMarketCode);

  const rightActive = bothSpot ? summary.right.length > 0 : summary.all.length > 0;
  const leftActive = bothSpot ? summary.left.length > 0 : summary.all.length > 0;
  const rightClass = rightActive ? "text-positive" : "text-negative/70";
  const leftClass = leftActive ? "text-positive" : "text-negative/70";

  const content = (
    <span className="inline-flex min-w-[20px] flex-col items-center justify-center gap-px rounded-md bg-surface-elevated/30 px-0.5 py-0.5 leading-[0.8]">
      <span className={`block text-[12px] font-bold ${rightClass}`}>→</span>
      <span className={`block text-[12px] font-bold ${leftClass}`}>←</span>
    </span>
  );

  if (!tooltipText) {
    return content;
  }

  return <Tooltip text={tooltipText}>{content}</Tooltip>;
}

function WalletStatusCellWrapper({ summary, tooltipText, targetMarketCode, originMarketCode, className = "" }) {
  return (
    <td className={`${CELL_MONO} text-center text-xs ${className}`}>
      <WalletStatusCell
        summary={summary}
        targetMarketCode={targetMarketCode}
        originMarketCode={originMarketCode}
        tooltipText={tooltipText}
      />
    </td>
  );
}

function fundingBadgeClass(hours) {
  switch (Number(hours)) {
    case 1:
      return "bg-positive/20 text-positive";
    case 2:
      return "bg-sky-500/20 text-sky-300";
    case 4:
      return "bg-amber-500/20 text-amber-200";
    case 8:
      return "bg-violet-500/20 text-violet-200";
    default:
      return "bg-surface-elevated text-ink-muted";
  }
}

function formatFundingCountdown(fundingTime, nowMs) {
  if (!fundingTime) {
    return "";
  }

  const targetMs = new Date(fundingTime).getTime();
  if (!Number.isFinite(targetMs)) {
    return "";
  }

  const diffMs = targetMs - nowMs;
  if (diffMs <= 0) {
    return "곧 갱신";
  }

  const totalSeconds = Math.floor(diffMs / 1000);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;

  return `${hours}시간 ${String(minutes).padStart(2, "0")}분 ${String(seconds).padStart(2, "0")}초 남음`;
}

function FundingRateCell({ funding, nowMs, className = "" }) {
  const value = funding?.funding_rate;
  const intervalHours = funding?.funding_interval_hours;
  const countdownLabel = formatFundingCountdown(funding?.funding_time, nowMs);

  return (
    <td className={`${CELL_MONO} text-right text-xs ${className}`}>
      <div className="inline-flex flex-col items-end gap-0.5">
        <div className="inline-flex items-center gap-1">
          <span className={polarityColor(value)}>
            {formatFundingPercent(value)}
          </span>
          {intervalHours != null ? (
            <span
              className={`rounded px-1.5 py-0.5 text-[10px] font-bold leading-none ${fundingBadgeClass(
                intervalHours
              )}`}
            >
              {intervalHours}h
            </span>
          ) : null}
        </div>
        {countdownLabel ? (
          <span className="text-[10px] italic text-ink-muted">{countdownLabel}</span>
        ) : null}
      </div>
    </td>
  );
}

function HighlightMatch({ text, query }) {
  if (!query) {
    return text;
  }

  const index = text.toLowerCase().indexOf(query.toLowerCase());

  if (index === -1) {
    return text;
  }

  return (
    <>
      {text.slice(0, index)}
      <mark className="rounded-sm bg-accent/30 px-0.5 text-ink">{text.slice(index, index + query.length)}</mark>
      {text.slice(index + query.length)}
    </>
  );
}

// Sort accessor functions
const SORT_ACCESSORS = {
  asset: (row) => row.base_asset || "",
  price: (row) => Number(row.tp || 0),
  enter: (row) => Number(row.LS_close || 0),
  exit: (row) => Number(row.SL_close || 0),
  spread: (row) => Number(row.SL_close || 0) - Number(row.LS_close || 0),
  volume: (row) => Number(row.atp24h || 0),
};

function sortRows(rows, sortKey, sortDirection, favoriteSet) {
  if (!sortKey) {
    return rows;
  }

  const accessor = SORT_ACCESSORS[sortKey];

  if (!accessor) {
    return rows;
  }

  const sorted = [...rows];

  sorted.sort((left, right) => {
    const leftFav = favoriteSet.has(left.base_asset);
    const rightFav = favoriteSet.has(right.base_asset);

    if (leftFav && !rightFav) return -1;
    if (!leftFav && rightFav) return 1;

    const leftVal = accessor(left);
    const rightVal = accessor(right);

    if (sortKey === "asset") {
      const cmp = String(leftVal).localeCompare(String(rightVal));
      return sortDirection === "asc" ? cmp : -cmp;
    }

    const diff = leftVal - rightVal;
    return sortDirection === "asc" ? diff : -diff;
  });

  return sorted;
}

const ICON_FALLBACK_COLORS = [
  "oklch(0.72 0.14 25)",
  "oklch(0.72 0.14 60)",
  "oklch(0.72 0.14 145)",
  "oklch(0.72 0.14 200)",
  "oklch(0.72 0.14 260)",
  "oklch(0.72 0.14 310)",
];

function iconFallbackColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i += 1) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return ICON_FALLBACK_COLORS[Math.abs(hash) % ICON_FALLBACK_COLORS.length];
}

// Responsive cell padding
const CELL = "px-1.5 py-1.5 sm:px-2 sm:py-1.5 lg:px-2.5 lg:py-2";
const CELL_MONO = `${CELL} tabular-nums`;

const PremiumTableRow = memo(
  function PremiumTableRow({
    asset,
    expanded,
    isEven,
    isOutlier,
    row,
    favoriteActive,
    iconUrl,
    isTetherPriceView,
    loggedIn,
    nowMs,
    onSelect,
    targetFunding,
    originFunding,
    showTargetFunding,
    showOriginFunding,
    volatilityMeanDiff,
    walletStatusSummary,
    walletStatusTooltip,
    targetMarketCode,
    originMarketCode,
    onToggleFavorite,
    searchQuery,
    aiLabel,
  }) {
    const lsClose = Number(row.LS_close || 0);
    const slClose = Number(row.SL_close || 0);
    const spread = slClose - lsClose;

    return (
      <tr
        className={`cursor-pointer border-l-2 transition-colors hover:bg-surface-elevated/70 ${
          expanded ? "border-l-accent bg-accent/5" : isOutlier ? "border-l-opportunity/40 bg-opportunity/[0.03]" : isEven ? "border-l-transparent bg-surface-elevated/[0.04]" : "border-l-transparent"
        }`}
        onClick={() => onSelect(asset)}
      >
        {/* ★ 즐겨찾기 — hidden mobile */}
        <td className={`${CELL} ${VIS.fav}`}>
          <button
            className="transition-colors"
            onClick={(event) => {
              event.stopPropagation();
              if (loggedIn) onToggleFavorite(asset);
            }}
            type="button"
          >
            <Star
              size={15}
              strokeWidth={2}
              className={`transition-all ${favoriteActive ? "fill-opportunity text-opportunity scale-110" : "text-ink-muted/40 hover:text-opportunity/60 hover:scale-110"}`}
            />
          </button>
        </td>

        {/* 자산 — always */}
        <td className={CELL}>
          <div className="grid gap-0.5">
            <div className="inline-flex items-center gap-1">
              <span className="asset-icon-plate" style={{ background: iconFallbackColor(asset) }}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  alt=""
                  className="asset-icon-plate__image"
                  loading="lazy"
                  onError={(e) => { e.currentTarget.style.display = "none"; }}
                  src={iconUrl || `https://assets.coincap.io/assets/icons/${asset.toLowerCase()}@2x.png`}
                />
                {asset.charAt(0)}
              </span>
              <strong className="text-ink text-[0.68rem] sm:text-xs">
                <HighlightMatch text={asset} query={searchQuery} />
              </strong>
              {aiLabel ? (
                <span className="hidden items-center rounded-full bg-accent/15 px-1.5 py-0.5 text-[0.54rem] font-bold text-accent sm:inline-flex">
                  {aiLabel}
                </span>
              ) : null}
              <ChevronRight
                className={`text-ink-muted transition-transform duration-200 ${expanded ? "rotate-90 text-accent" : ""}`}
                size={10}
                strokeWidth={2.5}
              />
            </div>
            {/* removed "차트 보기/숨기기" subtext — chevron already indicates expandability */}
          </div>
        </td>

        {/* 지갑 — always */}
        <WalletStatusCellWrapper
          summary={walletStatusSummary}
          targetMarketCode={targetMarketCode}
          originMarketCode={originMarketCode}
          tooltipText={walletStatusTooltip}
        />

        {/* 현재가 — always */}
        <td className={`${CELL_MONO} text-right whitespace-nowrap`}>
          <span className="text-xs font-semibold text-ink sm:text-sm">
            {formatNumber(row.tp, 1)}
          </span>
          <small className={`ml-0.5 text-[0.54rem] sm:text-[0.58rem] ${polarityColor(row.scr)}`}>
            {row.scr > 0 ? "+" : ""}
            {formatNumber(row.scr, 2, 2)}%
          </small>
        </td>

        {/* 진입김프/테더 — always */}
        <td
          className={`${CELL_MONO} text-right text-[0.68rem] sm:text-xs font-bold`}
          style={isTetherPriceView ? undefined : premiumColorStyle(lsClose)}
        >
          {isTetherPriceView ? formatTetherPrice(lsClose, row.dollar) : formatNumber(lsClose, 3, 3)}
        </td>

        {/* 탈출김프/테더 — hidden mobile */}
        <td
          className={`${CELL_MONO} text-right text-[0.68rem] sm:text-xs font-bold ${VIS.exit}`}
          style={isTetherPriceView ? undefined : premiumColorStyle(slClose)}
        >
          {isTetherPriceView ? formatTetherPrice(slClose, row.dollar) : formatNumber(slClose, 3, 3)}
        </td>

        {/* 스프레드 — always */}
        <td
          className={`${CELL_MONO} text-right text-[0.68rem] sm:text-xs font-bold`}
          style={premiumColorStyle(spread, 1)}
        >
          {`${spread > 0 ? "+" : ""}${formatNumber(spread, 2, 1)}%p`}
        </td>

        {/* 변동성 — desktop only */}
        <td
          className={`${CELL_MONO} text-right text-xs ${VIS.lgOnly}`}
          style={premiumColorStyle(volatilityMeanDiff, volatilityMeanDiff > 0 ? 1 : 0.5)}
        >
          {formatVolatility(volatilityMeanDiff)}
        </td>

        {/* 타겟 펀딩 — desktop only, hidden for spot */}
        {showTargetFunding ? (
          <FundingRateCell funding={targetFunding} nowMs={nowMs} className={VIS.lgOnly} />
        ) : null}

        {/* 오리진 펀딩 — desktop only, hidden for spot */}
        {showOriginFunding ? (
          <FundingRateCell funding={originFunding} nowMs={nowMs} className={VIS.lgOnly} />
        ) : null}

        {/* 거래액 — always */}
        <td className={`${CELL_MONO} text-right text-[0.68rem] sm:text-xs text-ink-muted`}>
          {formatKoreanVolume(row.atp24h)}
        </td>
      </tr>
    );
  },
  (previousProps, nextProps) =>
    previousProps.row === nextProps.row &&
    previousProps.expanded === nextProps.expanded &&
    previousProps.isEven === nextProps.isEven &&
    previousProps.isOutlier === nextProps.isOutlier &&
    previousProps.favoriteActive === nextProps.favoriteActive &&
    previousProps.iconUrl === nextProps.iconUrl &&
    previousProps.isTetherPriceView === nextProps.isTetherPriceView &&
    previousProps.loggedIn === nextProps.loggedIn &&
    previousProps.nowMs === nextProps.nowMs &&
    previousProps.showTargetFunding === nextProps.showTargetFunding &&
    previousProps.showOriginFunding === nextProps.showOriginFunding &&
    previousProps.targetFunding?.funding_rate === nextProps.targetFunding?.funding_rate &&
    previousProps.targetFunding?.funding_time === nextProps.targetFunding?.funding_time &&
    previousProps.targetFunding?.funding_interval_hours === nextProps.targetFunding?.funding_interval_hours &&
    previousProps.originFunding?.funding_rate === nextProps.originFunding?.funding_rate &&
    previousProps.originFunding?.funding_time === nextProps.originFunding?.funding_time &&
    previousProps.originFunding?.funding_interval_hours === nextProps.originFunding?.funding_interval_hours &&
    previousProps.volatilityMeanDiff === nextProps.volatilityMeanDiff &&
    previousProps.walletStatusTooltip === nextProps.walletStatusTooltip &&
    previousProps.targetMarketCode === nextProps.targetMarketCode &&
    previousProps.originMarketCode === nextProps.originMarketCode &&
    previousProps.searchQuery === nextProps.searchQuery &&
    previousProps.aiLabel === nextProps.aiLabel
);

// Column visibility classes matching PremiumTableRow order
const SKELETON_COL_VIS = [
  VIS.fav, "", "", "", "", VIS.exit, "",
  VIS.lgOnly, VIS.lgOnly, VIS.lgOnly, "",
];

function SkeletonRows() {
  return Array.from({ length: 8 }).map((_, i) => (
    <tr key={i}>
      {SKELETON_COL_VIS.map((vis, j) => (
        <td key={j} className={`${CELL} ${vis}`}>
          <div className="h-3 rounded bg-gradient-to-r from-border/20 via-border/40 to-border/20 bg-[length:200%_100%] animate-[shimmer_1.4s_linear_infinite]" />
        </td>
      ))}
    </tr>
  ));
}

function SortIcon({ active, direction }) {
  if (!active) {
    return <ChevronDown size={12} className="text-ink-muted/30 opacity-0 transition-opacity group-hover/sort:opacity-100" />;
  }

  return direction === "asc" ? (
    <ChevronUp size={12} className="text-accent" />
  ) : (
    <ChevronDown size={12} className="text-accent" />
  );
}

function SortableHeader({ children, className = "", visClass = "", sortKey, currentSortKey, sortDirection, onSort, tooltip }) {
  const isSortable = Boolean(sortKey);
  const isActive = isSortable && currentSortKey === sortKey;

  const content = (
    <button
      className={`group/sort inline-flex items-center gap-0.5 ${isSortable ? "cursor-pointer select-none hover:text-ink" : ""} ${isActive ? "text-accent" : ""}`}
      onClick={isSortable ? () => onSort(sortKey) : undefined}
      type="button"
    >
      {children}
      {isSortable ? <SortIcon active={isActive} direction={isActive ? sortDirection : "desc"} /> : null}
    </button>
  );

  return (
    <th className={`sticky top-0 z-1 px-1.5 py-2.5 sm:px-2 sm:py-3 lg:px-2.5 text-[0.62rem] sm:text-[0.66rem] font-bold uppercase tracking-wider shadow-[0_2px_4px_-1px_rgba(0,0,0,0.15)] transition-colors ${isActive ? "bg-background text-accent" : "bg-background text-ink-muted/80"} ${visClass} ${className}`}>
      {tooltip ? <Tooltip text={tooltip}>{content}</Tooltip> : content}
    </th>
  );
}

function formatTetherPrice(premiumPercent, dollarRate) {
  const premium = Number(premiumPercent || 0);
  const dollar = Number(dollarRate || 0);

  if (!dollar) {
    return "-";
  }

  const tetherPrice = dollar * (1 + premium * 0.01);

  return formatNumber(tetherPrice, 1);
}

export default function PremiumTable({
  displayRows,
  expandedAsset,
  onSelectAsset,
  onVisibleAssetsChange,
  favoriteMap,
  loggedIn,
  onToggleFavorite,
  targetFunding,
  originFunding,
  volatilityMap,
  walletStatus,
  targetMarketCode,
  originMarketCode,
  connected,
  searchQuery = "",
  aiRecommendations = [],
  isTetherPriceView = false,
  assetIcons = {},
}) {
  const tableRef = useRef(null);
  const [sortKey, setSortKey] = useState("");
  const [sortDirection, setSortDirection] = useState("desc");
  const [page, setPage] = useState(0);
  const [nowMs, setNowMs] = useState(() => Date.now());

  const showTargetFunding = !isSpotMarket(targetMarketCode);
  const showOriginFunding = !isSpotMarket(originMarketCode);

  const scrollToTable = useCallback(() => {
    tableRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const handleSort = useCallback(
    (key) => {
      if (key !== sortKey) {
        // New column: start descending
        setSortKey(key);
        setSortDirection("desc");
      } else if (sortDirection === "desc") {
        // Same column, desc → asc
        setSortDirection("asc");
      } else {
        // Same column, asc → clear
        setSortKey("");
        setSortDirection("desc");
      }
      setPage(0);
    },
    [sortKey, sortDirection]
  );

  const aiMap = useMemo(() => {
    const map = {};

    for (const rec of aiRecommendations) {
      if (rec.base_asset && rec.ai_label) {
        map[rec.base_asset] = rec.ai_label;
      }
    }

    return map;
  }, [aiRecommendations]);

  const favoriteSet = useMemo(
    () => new Set(Object.keys(favoriteMap).filter((key) => favoriteMap[key])),
    [favoriteMap]
  );

  const sortedRows = useMemo(
    () => sortRows(displayRows, sortKey, sortDirection, favoriteSet),
    [displayRows, sortKey, sortDirection, favoriteSet]
  );

  const totalPages = Math.max(1, Math.ceil(sortedRows.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages - 1);
  const paginatedRows = sortedRows.slice(safePage * PAGE_SIZE, (safePage + 1) * PAGE_SIZE);

  const visibleAssets = useMemo(
    () =>
      sortedRows
        .slice(safePage * PAGE_SIZE, Math.min(sortedRows.length, (safePage + 2) * PAGE_SIZE))
        .map((row) => row.base_asset)
        .filter(Boolean),
    [sortedRows, safePage]
  );

  useEffect(() => {
    if (!onVisibleAssetsChange) {
      return;
    }

    onVisibleAssetsChange(visibleAssets);
  }, [onVisibleAssetsChange, visibleAssets]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setNowMs(Date.now());
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, []);

  return (
    <div>
      <div ref={tableRef} className="overflow-x-auto rounded-lg border border-border bg-background/90">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b-2 border-border/70 bg-background">
              <SortableHeader className="text-left w-[36px]" visClass={VIS.fav} tooltip="즐겨찾기 등록/해제">
                <Star size={12} strokeWidth={2} />
              </SortableHeader>
              <SortableHeader className="text-left w-[10%]" sortKey="asset" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort}>
                자산
              </SortableHeader>
              <SortableHeader className="text-center w-[44px]" tooltip="지갑 입출금 가능 네트워크">
                지갑
              </SortableHeader>
              <SortableHeader className="text-right w-[1%] whitespace-nowrap" sortKey="price" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort}>
                현재가
              </SortableHeader>
              <SortableHeader className="text-right" sortKey="enter" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort} tooltip={isTetherPriceView ? "진입 테더 환산가" : "국내 매수 → 해외 선물 매도 시 프리미엄 (%)"}>
                {isTetherPriceView ? "진입테더" : "진입김프"}
              </SortableHeader>
              <SortableHeader className="text-right" visClass={VIS.exit} sortKey="exit" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort} tooltip={isTetherPriceView ? "탈출 테더 환산가" : "해외 선물 매수 → 국내 매도 시 프리미엄 (%)"}>
                {isTetherPriceView ? "탈출테더" : "탈출김프"}
              </SortableHeader>
              <SortableHeader className="text-right" sortKey="spread" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort} tooltip={isTetherPriceView ? "진입테더 - 탈출테더 차이" : "진입김프 - 탈출김프 차이 (%p)"}>
                스프레드
              </SortableHeader>
              <SortableHeader className="text-right" visClass={VIS.lgOnly} tooltip="최근 변동률 평균 대비 차이">
                변동성
              </SortableHeader>
              {showTargetFunding ? (
                <SortableHeader className="text-right" visClass={VIS.lgOnly}>
                  <span className="inline-flex items-center gap-1">
                    <ExchangeIcon exchange={extractExchange(targetMarketCode)} size={14} />
                    펀딩률
                  </span>
                </SortableHeader>
              ) : null}
              {showOriginFunding ? (
                <SortableHeader className="text-right" visClass={VIS.lgOnly}>
                  <span className="inline-flex items-center gap-1">
                    <ExchangeIcon exchange={extractExchange(originMarketCode)} size={14} />
                    펀딩률
                  </span>
                </SortableHeader>
              ) : null}
              <SortableHeader className="text-right" sortKey="volume" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort}>
                거래액(일)
              </SortableHeader>
            </tr>
          </thead>
          <tbody>
            {paginatedRows.length ? (
              paginatedRows.map((row, rowIndex) => {
                const asset = row.base_asset;
                const isFav = Boolean(favoriteMap[asset]);
                const prevRow = paginatedRows[rowIndex - 1];
                const prevIsFav = prevRow ? Boolean(favoriteMap[prevRow.base_asset]) : false;
                const isFavBoundary = !isFav && prevIsFav;
                const spread = Math.abs(Number(row.SL_close || 0) - Number(row.LS_close || 0));
                const isOutlier = spread >= 1;
                const targetFundingItem = targetFunding?.[asset]?.[0];
                const originFundingItem = originFunding?.[asset]?.[0];
                const volatilityItem = volatilityMap?.[asset];
                const walletStatusSummary = summarizeWalletStatus(
                  walletStatus,
                  targetMarketCode,
                  originMarketCode,
                  asset
                );
                const walletStatusTooltip = buildWalletStatusTooltip(
                  walletStatusSummary,
                  walletStatus,
                  targetMarketCode,
                  originMarketCode,
                  asset
                );

                return (
                  <Fragment key={asset}>
                    {isFavBoundary ? (
                      <tr><td colSpan="99" className="h-px bg-gradient-to-r from-transparent via-accent/20 to-transparent" /></tr>
                    ) : null}
                    <PremiumTableRow
                      aiLabel={aiMap[asset]}
                      asset={asset}
                      expanded={expandedAsset === asset}
                      isEven={rowIndex % 2 === 1}
                      isOutlier={isOutlier}
                      favoriteActive={isFav}
                      iconUrl={assetIcons[asset]}
                      isTetherPriceView={isTetherPriceView}
                      loggedIn={loggedIn}
                      nowMs={nowMs}
                      onSelect={onSelectAsset}
                      onToggleFavorite={onToggleFavorite}
                      originFunding={originFundingItem}
                      row={row}
                      searchQuery={searchQuery}
                      showTargetFunding={showTargetFunding}
                      showOriginFunding={showOriginFunding}
                      targetFunding={targetFundingItem}
                      walletStatusSummary={walletStatusSummary}
                      walletStatusTooltip={walletStatusTooltip}
                      targetMarketCode={targetMarketCode}
                      originMarketCode={originMarketCode}
                      volatilityMeanDiff={volatilityItem?.mean_diff}
                    />
                    {expandedAsset === asset ? (
                      <tr>
                        <td colSpan="99" className="p-0 bg-background/98">
                          <PremiumChartPanel
                            asset={asset}
                            isTetherPriceView={isTetherPriceView}
                            originFunding={originFundingItem}
                            originMarketCode={originMarketCode}
                            row={row}
                            targetFunding={targetFundingItem}
                            targetMarketCode={targetMarketCode}
                            walletNetworks={walletStatus?.[asset] || {}}
                            walletStatusSummary={walletStatusSummary}
                          />
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })
            ) : connected ? (
              <SkeletonRows />
            ) : (
              <tr>
                <td colSpan="99" className="px-4 py-12 text-center text-sm text-ink-muted">
                  실시간 프리미엄 데이터를 불러오는 중입니다...
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 ? (
        <div className="mt-2 flex items-center justify-center gap-3 px-1">
          <button
            className="rounded-md p-1.5 text-ink-muted transition-colors hover:bg-surface-elevated hover:text-ink disabled:opacity-30"
            disabled={safePage === 0}
            onClick={() => { setPage((p) => p - 1); scrollToTable(); }}
            type="button"
          >
            <ChevronLeft size={16} strokeWidth={2} />
          </button>
          <div className="flex items-center gap-1">
            {Array.from({ length: totalPages }).map((_, i) => (
              <button
                key={i}
                className={`h-1.5 rounded-full transition-all ${
                  i === safePage
                    ? "w-5 bg-accent"
                    : "w-1.5 bg-ink-muted/30 hover:bg-ink-muted/50"
                }`}
                onClick={() => { setPage(i); scrollToTable(); }}
                type="button"
                aria-label={`${i + 1}페이지`}
              />
            ))}
          </div>
          <button
            className="rounded-md p-1.5 text-ink-muted transition-colors hover:bg-surface-elevated hover:text-ink disabled:opacity-30"
            disabled={safePage >= totalPages - 1}
            onClick={() => { setPage((p) => p + 1); scrollToTable(); }}
            type="button"
          >
            <ChevronRight size={16} strokeWidth={2} />
          </button>
          <span className="text-[0.6rem] tabular-nums text-ink-muted/50">{safePage + 1}/{totalPages}</span>
        </div>
      ) : null}
    </div>
  );
}
