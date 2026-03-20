"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRightLeft, ChevronDown, Search } from "lucide-react";

function prettifyMarketCode(code) {
  return code?.replaceAll("_", " ") || "";
}

const EXCHANGE_LABELS = {
  UPBIT: "업비트",
  BITHUMB: "빗썸",
  COINONE: "코인원",
  BINANCE: "바이낸스",
  BYBIT: "바이빗",
  OKX: "OKX",
  GATE: "Gate",
  HYPERLIQUID: "Hyperliquid",
};

const EXCHANGE_SHORT = {
  UPBIT: "UP",
  BITHUMB: "BT",
  COINONE: "CO",
  BINANCE: "BI",
  BYBIT: "BY",
  OKX: "OK",
  GATE: "GT",
  HYPERLIQUID: "HL",
};

function parseMarketCode(code) {
  if (!code) {
    return {
      code: "",
      exchange: "",
      exchangeLabel: "",
      productLabel: "",
      quoteAsset: "",
      shortLabel: "",
    };
  }

  const [marketPart = "", quoteAsset = ""] = code.split("/");
  const [exchange = "", ...rest] = marketPart.split("_");
  const product = rest.join("_");
  const isSpot = product === "SPOT";

  return {
    code,
    exchange,
    exchangeLabel: EXCHANGE_LABELS[exchange] || exchange,
    exchangeShort: EXCHANGE_SHORT[exchange] || exchange.slice(0, 2),
    productLabel: isSpot ? "Spot" : product.replaceAll("_", "-"),
    quoteAsset,
    shortLabel: `${EXCHANGE_LABELS[exchange] || exchange} ${isSpot ? "Spot" : product.replaceAll("_", "-")}`,
  };
}

function pairPriority(targetCode, originCode) {
  let score = 0;

  if (targetCode.includes("KRW")) {
    score += 100;
  }
  if (originCode.includes("USD_M")) {
    score += 60;
  }
  if (originCode.includes("USDT")) {
    score += 30;
  }
  if (originCode.includes("USDC")) {
    score += 20;
  }
  if (targetCode.includes("SPOT")) {
    score += 10;
  }

  return score;
}

const BADGE_COLORS = {
  upbit: "bg-[#0a4abf] text-white",
  bithumb: "bg-[#f37321] text-white",
  coinone: "bg-[#0062df] text-white",
  binance: "bg-[#f0b90b] text-black",
  bybit: "bg-[#f7a600] text-black",
  okx: "bg-white text-black",
  gate: "bg-[#2354e6] text-white",
  hyperliquid: "bg-[#6ee7b7] text-black",
};

function ExchangeBadge({ exchange, size = "sm" }) {
  const px = size === "sm" ? 18 : 22;
  const key = exchange?.toLowerCase() || "";
  const short = EXCHANGE_SHORT[exchange] || exchange.slice(0, 2);
  const colorClass = BADGE_COLORS[key] || "bg-ink-muted/20 text-ink";

  return (
    <span className="inline-flex flex-shrink-0">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        alt={exchange}
        className="rounded-md"
        height={px}
        width={px}
        src={`/images/exchanges/${key}.svg`}
        onError={(e) => { e.currentTarget.style.display = "none"; e.currentTarget.nextSibling.style.display = "flex"; }}
      />
      <span
        className={`items-center justify-center rounded-md font-bold ${colorClass}`}
        style={{ width: px, height: px, fontSize: px * 0.42, display: "none" }}
      >
        {short}
      </span>
    </span>
  );
}

export default function MarketCombinationPicker({
  marketCodes,
  onOriginChange,
  onTargetChange,
  originMarketCode,
  targetMarketCode,
}) {
  const rootRef = useRef(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [draftTarget, setDraftTarget] = useState(targetMarketCode || "");

  const targetOptions = useMemo(
    () =>
      Object.keys(marketCodes || {}).map((code) => ({
        ...parseMarketCode(code),
        origins: marketCodes?.[code] || [],
      })),
    [marketCodes]
  );

  const activeDraftTarget = useMemo(() => {
    if (draftTarget && marketCodes?.[draftTarget]) {
      return draftTarget;
    }

    return targetMarketCode || targetOptions[0]?.code || "";
  }, [draftTarget, marketCodes, targetMarketCode, targetOptions]);

  useEffect(() => {
    if (!open) {
      return undefined;
    }

    function handlePointerDown(event) {
      if (rootRef.current && !rootRef.current.contains(event.target)) {
        setOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    window.addEventListener("pointerdown", handlePointerDown);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("pointerdown", handlePointerDown);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const selectedTarget = useMemo(() => parseMarketCode(targetMarketCode), [targetMarketCode]);
  const selectedOrigin = useMemo(() => parseMarketCode(originMarketCode), [originMarketCode]);

  const filteredTargets = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return targetOptions.filter((option) => {
      if (!normalizedQuery) {
        return true;
      }

      return [
        option.exchangeLabel,
        option.productLabel,
        option.quoteAsset,
        option.code,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [query, targetOptions]);

  const draftOriginOptions = useMemo(
    () =>
      (marketCodes?.[activeDraftTarget] || []).map((code) => ({
        ...parseMarketCode(code),
      })),
    [activeDraftTarget, marketCodes]
  );

  const quickPairs = useMemo(() => {
    const pairs = [];

    Object.entries(marketCodes || {}).forEach(([target, origins]) => {
      origins.forEach((origin) => {
        pairs.push({
          target,
          origin,
          score: pairPriority(target, origin),
        });
      });
    });

    return pairs
      .sort((left, right) => right.score - left.score)
      .slice(0, 6)
      .map((pair) => ({
        ...pair,
        targetMeta: parseMarketCode(pair.target),
        originMeta: parseMarketCode(pair.origin),
      }));
  }, [marketCodes]);

  return (
    <div className="relative" ref={rootRef}>
      {/* Compact pill trigger */}
      <button
        className={`inline-flex items-center gap-1 sm:gap-1.5 whitespace-nowrap rounded-lg border px-1.5 sm:px-2 py-1 sm:py-1.5 text-[0.68rem] sm:text-sm font-semibold transition-colors ${
          open
            ? "border-accent/40 bg-accent/10 text-ink"
            : "border-border bg-background/70 text-ink hover:border-border/80 hover:bg-surface-elevated/40"
        }`}
        onClick={() => {
          if (open) {
            setOpen(false);
            return;
          }

          setDraftTarget(targetMarketCode || targetOptions[0]?.code || "");
          setQuery("");
          setOpen(true);
        }}
        type="button"
      >
        {selectedTarget.code ? (
          <>
            <ExchangeBadge exchange={selectedTarget.exchange} />
            <span className="text-ink hidden sm:inline">{selectedTarget.exchangeLabel}</span>
            <ArrowRightLeft className="text-ink-muted" size={12} strokeWidth={2} />
            <ExchangeBadge exchange={selectedOrigin.exchange} />
            <span className="text-ink">
              <span className="hidden sm:inline">{selectedOrigin.exchangeLabel} </span>{selectedOrigin.productLabel}/{selectedOrigin.quoteAsset}
            </span>
          </>
        ) : (
          <span className="text-ink-muted">시장 조합 선택</span>
        )}
        <ChevronDown
          className={`ml-0.5 text-ink-muted transition-transform ${open ? "rotate-180" : ""}`}
          size={12}
          strokeWidth={2}
        />
      </button>

      {/* Dropdown panel */}
      {open ? (
        <div className="absolute left-0 top-full z-50 mt-1 w-[min(640px,calc(100vw-32px))] rounded-xl border border-border bg-background shadow-2xl" style={{ animation: "fadeSlideUp 0.2s cubic-bezier(0.16, 1, 0.3, 1)" }}>
          {/* Search */}
          <div className="flex items-center gap-2 border-b border-border px-3 py-2.5">
            <Search className="text-ink-muted" size={14} strokeWidth={2} />
            <input
              className="flex-1 bg-transparent text-sm text-ink placeholder:text-ink-muted/60 outline-none"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="거래소 또는 마켓 검색"
              value={query}
            />
          </div>

          {/* Quick pairs */}
          <div className="flex flex-wrap gap-1.5 border-b border-border px-3 py-2">
            {quickPairs.map((pair) => (
              <button
                className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[0.68rem] cursor-pointer font-semibold transition-colors ${
                  targetMarketCode === pair.target && originMarketCode === pair.origin
                    ? "border-accent/30 bg-accent/10 text-accent"
                    : "border-border bg-background/70 text-ink-muted hover:bg-accent/10 hover:border-accent/30 hover:text-ink transition-all duration-150"
                }`}
                key={`${pair.target}-${pair.origin}`}
                onClick={() => {
                  onTargetChange(pair.target);
                  onOriginChange(pair.origin);
                  setOpen(false);
                }}
                type="button"
              >
                <ExchangeBadge exchange={pair.targetMeta.exchange} size="sm" />
                <span>{pair.targetMeta.quoteAsset}</span>
                <ArrowRightLeft className="text-ink-muted/50" size={10} strokeWidth={2} />
                <ExchangeBadge exchange={pair.originMeta.exchange} size="sm" />
                <span>{pair.originMeta.productLabel}</span>
              </button>
            ))}
          </div>

          {/* Two-column grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-border">
            <div className="flex flex-col">
              <div className="flex items-center justify-between px-3 py-2.5 text-[0.64rem] font-bold tracking-wide text-accent/70">
                <span>기준거래소</span>
                <span className="tabular-nums">{filteredTargets.length}</span>
              </div>
              <div className="max-h-[280px] overflow-y-auto">
                {filteredTargets.map((option) => (
                  <button
                    className={`flex w-full items-center gap-2.5 border-l-2 px-3 py-2.5 text-left text-xs transition-all cursor-pointer ${
                      activeDraftTarget === option.code
                        ? "border-l-accent bg-accent/10 text-ink hover:bg-accent/15"
                        : "border-l-transparent text-ink-muted hover:bg-accent/8 hover:border-l-accent/40 hover:text-ink"
                    }`}
                    key={option.code}
                    onClick={() => setDraftTarget(option.code)}
                    type="button"
                  >
                    <ExchangeBadge exchange={option.exchange} />
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold truncate">{option.exchangeLabel}</div>
                      <div className="text-[0.6rem] text-ink-muted/60">{option.productLabel}/{option.quoteAsset}</div>
                    </div>
                    <ArrowRightLeft size={12} className="text-ink-muted/30 flex-shrink-0" />
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col">
              <div className="flex items-center justify-between px-3 py-2.5 text-[0.64rem] font-bold tracking-wide text-accent/70">
                <span>비교거래소</span>
                <span className="tabular-nums">{draftOriginOptions.length}</span>
              </div>
              <div className="max-h-[280px] overflow-y-auto">
                {draftOriginOptions.map((option) => (
                  <button
                    className={`flex w-full items-center gap-2.5 border-l-2 px-3 py-2.5 text-left text-xs transition-all cursor-pointer ${
                      originMarketCode === option.code
                        ? "border-l-accent bg-accent/10 text-ink hover:bg-accent/15"
                        : "border-l-transparent text-ink-muted hover:bg-accent/8 hover:border-l-accent/40 hover:text-ink"
                    }`}
                    key={option.code}
                    onClick={() => {
                      onTargetChange(activeDraftTarget);
                      onOriginChange(option.code);
                      setOpen(false);
                    }}
                    type="button"
                  >
                    <ExchangeBadge exchange={option.exchange} />
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold truncate">{option.exchangeLabel}</div>
                      <div className="text-[0.6rem] text-ink-muted/60">{option.productLabel}/{option.quoteAsset}</div>
                    </div>
                    {originMarketCode === option.code && <span className="text-accent text-[0.7rem]">✓</span>}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
