"use client";

import { Fragment, memo, useCallback, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, ChevronUp } from "lucide-react";

import { premiumHeatmap, spreadHeatmap } from "../../lib/heatmap";
import PremiumChartPanel from "./PremiumChartPanel";
import Tooltip from "../ui/Tooltip";

const PAGE_SIZE = 50;

// Responsive visibility classes per column
// mobile(<640): 자산, 현재가, 진입김프, 스프레드, 거래액 (5 cols)
// tablet(640-1024): + 즐겨찾기, 탈출김프 (7 cols)
// desktop(>1024): all 11 cols
const VIS = {
  fav: "hidden sm:table-cell",
  exit: "hidden sm:table-cell",
  lgOnly: "hidden lg:table-cell",
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

function formatVolatility(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return Number(value).toFixed(3);
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

function hasTransferRoute(walletStatus, targetMarketCode, originMarketCode, asset) {
  const assetStatus = walletStatus?.[asset];
  if (!assetStatus) {
    return false;
  }

  const targetExchange = targetMarketCode.split("_")[0];
  const originExchange = originMarketCode.split("_")[0];

  const withdrawNetworks = assetStatus?.[targetExchange]?.withdraw || [];
  const depositNetworks = assetStatus?.[originExchange]?.deposit || [];

  return withdrawNetworks.some((network) => depositNetworks.includes(network));
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

// Responsive cell padding
const CELL = "px-1.5 py-1.5 sm:px-2 sm:py-1.5 lg:px-2.5 lg:py-2";
const CELL_MONO = `${CELL} tabular-nums font-mono`;

const PremiumTableRow = memo(
  function PremiumTableRow({
    asset,
    expanded,
    row,
    favoriteActive,
    loggedIn,
    onSelect,
    targetFundingRate,
    originFundingRate,
    volatilityMeanDiff,
    transferAvailable,
    onToggleFavorite,
    searchQuery,
    aiLabel,
  }) {
    const lsClose = Number(row.LS_close || 0);
    const slClose = Number(row.SL_close || 0);
    const spread = slClose - lsClose;

    return (
      <tr
        className={`cursor-pointer border-l-2 transition-colors hover:bg-surface-elevated/50 ${
          expanded ? "border-l-accent bg-surface-elevated/30" : "border-l-transparent"
        }`}
        onClick={() => onSelect(asset)}
      >
        {/* ★ 즐겨찾기 — hidden mobile */}
        <td className={`${CELL} ${VIS.fav}`}>
          <button
            className={`text-sm transition-colors ${favoriteActive ? "text-opportunity" : "text-ink-muted/50"} disabled:opacity-40`}
            disabled={!loggedIn}
            onClick={(event) => {
              event.stopPropagation();
              onToggleFavorite(asset);
            }}
            type="button"
          >
            ★
          </button>
        </td>

        {/* 자산 — always */}
        <td className={CELL}>
          <div className="grid gap-0.5">
            <div className="inline-flex items-center gap-1">
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
            <small className="text-[0.56rem] sm:text-[0.6rem] text-ink-muted">{expanded ? "차트 숨기기" : "차트 보기"}</small>
          </div>
        </td>

        {/* 현재가 — always */}
        <td className={`${CELL_MONO} text-right`}>
          <div className="text-xs font-semibold text-ink sm:text-sm">
            {formatNumber(row.tp, 1)}
          </div>
          <small className={`text-[0.58rem] sm:text-[0.64rem] ${polarityColor(row.scr)}`}>
            {row.scr > 0 ? "+" : ""}
            {formatNumber(row.scr, 2, 2)}%
          </small>
        </td>

        {/* 진입김프 — always */}
        <td
          className={`${CELL_MONO} text-right text-[0.68rem] sm:text-xs ${polarityColor(lsClose)}`}
          style={{ backgroundColor: premiumHeatmap(lsClose) }}
        >
          {formatNumber(lsClose, 2, 2)}
        </td>

        {/* 탈출김프 — hidden mobile */}
        <td
          className={`${CELL_MONO} text-right text-[0.68rem] sm:text-xs ${VIS.exit} ${polarityColor(slClose)}`}
          style={{ backgroundColor: premiumHeatmap(slClose) }}
        >
          {formatNumber(slClose, 2, 2)}
        </td>

        {/* 스프레드 — always */}
        <td
          className={`${CELL_MONO} text-right text-[0.68rem] sm:text-xs ${polarityColor(spread)}`}
          style={{ backgroundColor: spreadHeatmap(spread) }}
        >
          {spread > 0 ? "+" : ""}
          {formatNumber(spread, 2, 1)}%p
        </td>

        {/* 변동성 — desktop only */}
        <td className={`${CELL_MONO} text-right text-xs text-ink-muted ${VIS.lgOnly}`}>
          {formatVolatility(volatilityMeanDiff)}
        </td>

        {/* 타겟 펀딩 — desktop only */}
        <td className={`${CELL_MONO} text-right text-xs ${VIS.lgOnly} ${polarityColor(targetFundingRate)}`}>
          {formatPercent(targetFundingRate)}
        </td>

        {/* 오리진 펀딩 — desktop only */}
        <td className={`${CELL_MONO} text-right text-xs ${VIS.lgOnly} ${polarityColor(originFundingRate)}`}>
          {formatPercent(originFundingRate)}
        </td>

        {/* 전송 — desktop only */}
        <td className={`${CELL_MONO} text-right text-xs ${VIS.lgOnly} ${transferAvailable ? "text-positive" : "text-ink-muted"}`}>
          {transferAvailable ? "가능" : "-"}
        </td>

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
    previousProps.favoriteActive === nextProps.favoriteActive &&
    previousProps.loggedIn === nextProps.loggedIn &&
    previousProps.targetFundingRate === nextProps.targetFundingRate &&
    previousProps.originFundingRate === nextProps.originFundingRate &&
    previousProps.volatilityMeanDiff === nextProps.volatilityMeanDiff &&
    previousProps.transferAvailable === nextProps.transferAvailable &&
    previousProps.searchQuery === nextProps.searchQuery &&
    previousProps.aiLabel === nextProps.aiLabel
);

// Column visibility classes matching PremiumTableRow order
const SKELETON_COL_VIS = [
  VIS.fav, "", "", "", VIS.exit, "",
  VIS.lgOnly, VIS.lgOnly, VIS.lgOnly, VIS.lgOnly, "",
];

function SkeletonRows() {
  return Array.from({ length: 8 }).map((_, i) => (
    <tr key={i}>
      {SKELETON_COL_VIS.map((vis, j) => (
        <td key={j} className={`${CELL} ${vis}`}>
          <div className="h-3 animate-pulse rounded bg-border/30" />
        </td>
      ))}
    </tr>
  ));
}

function SortIcon({ active, direction }) {
  if (!active) {
    return <ChevronDown size={9} className="text-ink-muted/40" />;
  }

  return direction === "asc" ? (
    <ChevronUp size={9} className="text-accent" />
  ) : (
    <ChevronDown size={9} className="text-accent" />
  );
}

function SortableHeader({ children, className = "", visClass = "", sortKey, currentSortKey, sortDirection, onSort, tooltip }) {
  const isSortable = Boolean(sortKey);
  const isActive = currentSortKey === sortKey;

  const content = (
    <button
      className={`inline-flex items-center gap-0.5 ${isSortable ? "cursor-pointer select-none hover:text-ink" : ""}`}
      onClick={isSortable ? () => onSort(sortKey) : undefined}
      type="button"
    >
      {children}
      {isSortable ? <SortIcon active={isActive} direction={isActive ? sortDirection : "desc"} /> : null}
    </button>
  );

  return (
    <th className={`sticky top-0 z-1 px-1.5 py-1.5 sm:px-2 sm:py-2 lg:px-2.5 text-[0.54rem] sm:text-[0.58rem] lg:text-[0.62rem] font-bold uppercase tracking-wider text-ink-muted ${visClass} ${className}`}>
      {tooltip ? <Tooltip text={tooltip}>{content}</Tooltip> : content}
    </th>
  );
}

export default function PremiumTable({
  displayRows,
  expandedAsset,
  onSelectAsset,
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
}) {
  const [sortKey, setSortKey] = useState("");
  const [sortDirection, setSortDirection] = useState("desc");
  const [page, setPage] = useState(0);

  const handleSort = useCallback((key) => {
    setSortKey((prev) => {
      if (prev === key) {
        setSortDirection((dir) => (dir === "desc" ? "asc" : "desc"));
        return key;
      }

      setSortDirection("desc");
      return key;
    });
    setPage(0);
  }, []);

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

  return (
    <div>
      <div className="overflow-x-auto rounded-lg border border-border bg-background/90">
        <table className="w-full lg:min-w-[980px] border-collapse">
          <thead>
            <tr className="border-b border-border bg-background/98">
              <SortableHeader className="text-left" visClass={VIS.fav} tooltip="즐겨찾기 등록/해제">
                즐겨찾기
              </SortableHeader>
              <SortableHeader className="text-left" sortKey="asset" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort}>
                자산
              </SortableHeader>
              <SortableHeader className="text-right" sortKey="price" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort}>
                현재가
              </SortableHeader>
              <SortableHeader className="text-right" sortKey="enter" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort} tooltip="국내 매수 → 해외 선물 매도 시 프리미엄 (%)">
                진입김프
              </SortableHeader>
              <SortableHeader className="text-right" visClass={VIS.exit} sortKey="exit" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort} tooltip="해외 선물 매수 → 국내 매도 시 프리미엄 (%)">
                탈출김프
              </SortableHeader>
              <SortableHeader className="text-right" sortKey="spread" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort} tooltip="진입김프 - 탈출김프 차이 (%p)">
                스프레드
              </SortableHeader>
              <SortableHeader className="text-right" visClass={VIS.lgOnly} tooltip="최근 변동률 평균 대비 차이">
                변동성
              </SortableHeader>
              <SortableHeader className="text-right" visClass={VIS.lgOnly}>
                타겟 펀딩
              </SortableHeader>
              <SortableHeader className="text-right" visClass={VIS.lgOnly}>
                오리진 펀딩
              </SortableHeader>
              <SortableHeader className="text-right" visClass={VIS.lgOnly}>
                전송
              </SortableHeader>
              <SortableHeader className="text-right" sortKey="volume" currentSortKey={sortKey} sortDirection={sortDirection} onSort={handleSort}>
                거래액(24h)
              </SortableHeader>
            </tr>
          </thead>
          <tbody>
            {paginatedRows.length ? (
              paginatedRows.map((row) => {
                const asset = row.base_asset;
                const targetFundingItem = targetFunding?.[asset]?.[0];
                const originFundingItem = originFunding?.[asset]?.[0];
                const volatilityItem = volatilityMap?.[asset];
                const transferAvailable = hasTransferRoute(
                  walletStatus,
                  targetMarketCode,
                  originMarketCode,
                  asset
                );

                return (
                  <Fragment key={asset}>
                    <PremiumTableRow
                      aiLabel={aiMap[asset]}
                      asset={asset}
                      expanded={expandedAsset === asset}
                      favoriteActive={Boolean(favoriteMap[asset])}
                      loggedIn={loggedIn}
                      onSelect={onSelectAsset}
                      onToggleFavorite={onToggleFavorite}
                      originFundingRate={originFundingItem?.funding_rate}
                      row={row}
                      searchQuery={searchQuery}
                      targetFundingRate={targetFundingItem?.funding_rate}
                      transferAvailable={transferAvailable}
                      volatilityMeanDiff={volatilityItem?.mean_diff}
                    />
                    {expandedAsset === asset ? (
                      <tr>
                        <td colSpan="99" className="p-0 bg-background/98">
                          <PremiumChartPanel
                            asset={asset}
                            originFundingRate={originFundingItem?.funding_rate}
                            originMarketCode={originMarketCode}
                            row={row}
                            targetFundingRate={targetFundingItem?.funding_rate}
                            targetMarketCode={targetMarketCode}
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
        <div className="mt-2 flex items-center justify-between px-1">
          <span className="text-[0.68rem] sm:text-xs text-ink-muted">
            {sortedRows.length}개 중 {safePage * PAGE_SIZE + 1}–{Math.min((safePage + 1) * PAGE_SIZE, sortedRows.length)}
          </span>
          <div className="flex items-center gap-0.5 sm:gap-1">
            <button
              className="rounded px-2 py-1 text-[0.68rem] sm:text-xs font-semibold text-ink-muted transition-colors hover:bg-surface-elevated hover:text-ink disabled:opacity-40"
              disabled={safePage === 0}
              onClick={() => setPage((p) => p - 1)}
              type="button"
            >
              이전
            </button>
            {Array.from({ length: totalPages }).map((_, i) => (
              <button
                key={i}
                className={`rounded px-1.5 py-1 text-[0.68rem] sm:text-xs font-semibold transition-colors ${
                  i === safePage
                    ? "bg-accent/20 text-accent"
                    : "text-ink-muted hover:bg-surface-elevated hover:text-ink"
                }`}
                onClick={() => setPage(i)}
                type="button"
              >
                {i + 1}
              </button>
            ))}
            <button
              className="rounded px-2 py-1 text-[0.68rem] sm:text-xs font-semibold text-ink-muted transition-colors hover:bg-surface-elevated hover:text-ink disabled:opacity-40"
              disabled={safePage >= totalPages - 1}
              onClick={() => setPage((p) => p + 1)}
              type="button"
            >
              다음
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
