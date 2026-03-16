"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRightLeft, ChevronDown, Search } from "lucide-react";

import ExchangeIcon from "../ui/ExchangeIcon";

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
        className={`inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-sm font-semibold transition-all ${
          open
            ? "border-accent/40 bg-accent/10 text-ink shadow-[0_0_12px_-3px_rgba(43,115,255,0.35)]"
            : selectedTarget.code
              ? "border-border bg-background/70 text-ink shadow-[0_0_8px_-4px_rgba(43,115,255,0.2)] hover:border-accent/30 hover:shadow-[0_0_12px_-3px_rgba(43,115,255,0.3)]"
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
            <ExchangeIcon exchange={selectedTarget.exchange} size={20} />
            <span className="text-ink">{selectedTarget.exchangeLabel}</span>
            <ArrowRightLeft className="text-ink-muted" size={14} strokeWidth={2} />
            <ExchangeIcon exchange={selectedOrigin.exchange} size={20} />
            <span className="text-ink">
              {selectedOrigin.exchangeLabel} {selectedOrigin.productLabel}/{selectedOrigin.quoteAsset}
            </span>
          </>
        ) : (
          <span className="text-ink-muted">시장 조합 선택</span>
        )}
        <ChevronDown
          className={`ml-1 text-ink-muted transition-transform ${open ? "rotate-180" : ""}`}
          size={14}
          strokeWidth={2}
        />
      </button>

      {/* Dropdown panel */}
      {open ? (
        <div className="absolute left-0 top-full z-30 mt-1 w-[min(640px,calc(100vw-32px))] rounded-xl border border-border bg-background shadow-2xl" style={{ animation: "riseIn 200ms cubic-bezier(0.4, 0, 0.15, 1) both" }}>
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
                className={`inline-flex items-center gap-1 rounded-md border px-2 py-1 text-[0.68rem] font-semibold transition-colors ${
                  targetMarketCode === pair.target && originMarketCode === pair.origin
                    ? "border-accent/30 bg-accent/10 text-accent"
                    : "border-border bg-background/70 text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
                }`}
                key={`${pair.target}-${pair.origin}`}
                onClick={() => {
                  onTargetChange(pair.target);
                  onOriginChange(pair.origin);
                  setOpen(false);
                }}
                type="button"
              >
                <ExchangeIcon exchange={pair.targetMeta.exchange} size={16} />
                <span>{pair.targetMeta.quoteAsset}</span>
                <ArrowRightLeft className="text-ink-muted/50" size={10} strokeWidth={2} />
                <ExchangeIcon exchange={pair.originMeta.exchange} size={16} />
                <span>{pair.originMeta.productLabel}</span>
              </button>
            ))}
          </div>

          {/* Two-column grid */}
          <div className="grid grid-cols-2 divide-x divide-border">
            <div className="flex flex-col">
              <div className="flex items-center justify-between px-3 py-2 text-[0.62rem] font-bold uppercase tracking-wider text-ink-muted">
                <span>타겟 시장</span>
                <span className="tabular-nums">{filteredTargets.length}</span>
              </div>
              <div className="max-h-[280px] overflow-y-auto">
                {filteredTargets.map((option) => (
                  <button
                    className={`flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition-colors ${
                      activeDraftTarget === option.code
                        ? "bg-accent/10 text-ink"
                        : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
                    }`}
                    key={option.code}
                    onClick={() => setDraftTarget(option.code)}
                    type="button"
                  >
                    <ExchangeIcon exchange={option.exchange} size={20} />
                    <div>
                      <div className="font-semibold">{option.exchangeLabel}</div>
                      <div className="text-[0.6rem] text-ink-muted">{option.productLabel}/{option.quoteAsset}</div>
                    </div>
                    <span className="ml-auto text-[0.58rem] tabular-nums text-ink-muted/60">{option.origins.length}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="flex flex-col">
              <div className="flex items-center justify-between px-3 py-2 text-[0.62rem] font-bold uppercase tracking-wider text-ink-muted">
                <span>오리진 시장</span>
                <span className="tabular-nums">{draftOriginOptions.length}</span>
              </div>
              <div className="max-h-[280px] overflow-y-auto">
                {draftOriginOptions.map((option) => (
                  <button
                    className={`flex w-full items-center gap-2 px-3 py-2 text-left text-xs transition-colors ${
                      originMarketCode === option.code
                        ? "bg-accent/10 text-ink"
                        : "text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
                    }`}
                    key={option.code}
                    onClick={() => {
                      onTargetChange(activeDraftTarget);
                      onOriginChange(option.code);
                      setOpen(false);
                    }}
                    type="button"
                  >
                    <ExchangeIcon exchange={option.exchange} size={20} />
                    <div>
                      <div className="font-semibold">{option.exchangeLabel}</div>
                      <div className="text-[0.6rem] text-ink-muted">{option.productLabel}/{option.quoteAsset}</div>
                    </div>
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
