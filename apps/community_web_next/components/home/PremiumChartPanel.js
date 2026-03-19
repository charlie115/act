"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ChartCandlestick, ChartLine } from "lucide-react";

import { CandlestickSeries, createChart, LineSeries } from "../../lib/vendor/lightweight-charts.js";
import { fetchCachedJson, getKlineCache, setKlineCache } from "../../lib/clientCache";
import { getBrowserTimezone } from "../../lib/constants";
import ExchangeIcon from "../ui/ExchangeIcon";

const DATA_MODES = [
  { label: "김프", value: "premium" },
  { label: "진입", value: "entry" },
  { label: "탈출", value: "exit" },
];

const INTERVALS = [
  { label: "1m", value: "1T" },
  { label: "15m", value: "15T" },
  { label: "1h", value: "1H" },
  { label: "4h", value: "4H" },
  { label: "1D", value: "1D" },
];

const INTERVAL_SECONDS = {
  "1T": 60,
  "15T": 900,
  "1H": 3600,
  "4H": 14400,
  "1D": 86400,
};

const HISTORY_INITIAL_LIMIT = 500;
const HISTORY_OLDER_LIMIT = 500;
const HISTORY_LOAD_THRESHOLD = 50;
const INITIAL_VISIBLE_BARS = 180;
const INITIAL_RIGHT_OFFSET_BARS = 6;

function formatNumber(value, maximumFractionDigits = 3) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits,
    minimumFractionDigits: 0,
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

function polarityColor(value) {
  const n = Number(value || 0);
  if (n > 0) return "text-positive";
  if (n < 0) return "text-negative";
  return "text-ink-muted";
}

function formatCompactPrice(price) {
  if (!Number.isFinite(price)) return "-";
  const abs = Math.abs(price);
  if (abs >= 1_0000_0000) return `${(price / 1_0000_0000).toFixed(3)}억`;
  if (abs >= 100_0000) return `${(price / 1_0000).toFixed(0)}만`;
  if (abs >= 1_0000) return `${(price / 1_0000).toFixed(1)}만`;
  if (abs >= 1) return price.toFixed(1);
  return price.toPrecision(4);
}

// lightweight-charts displays time in UTC; shift timestamps by the local
// timezone offset so the X-axis shows the browser's local time.
function toLocalChartTime(dateMs) {
  const offsetSeconds = -new Date(dateMs).getTimezoneOffset() * 60;
  return Math.floor(dateMs / 1000) + offsetSeconds;
}

// Pre-compute chart timestamps from history rows (avoids repeated new Date() calls)
function precomputeTimestamps(points) {
  return points.map((item) => {
    if (!item?.datetime_now) return { item, time: NaN };
    const time = toLocalChartTime(new Date(item.datetime_now).getTime());
    return { item, time };
  });
}

function makeTimeSeries(cached, key) {
  const result = [];
  for (let i = 0; i < cached.length; i++) {
    const { item, time } = cached[i];
    if (!Number.isFinite(time)) continue;
    const value = Number(item?.[key]);
    if (!Number.isFinite(value)) continue;
    result.push({ time, value });
  }
  return result;
}

function makeCandlestickSeries(cached, prefix) {
  const result = [];
  for (let i = 0; i < cached.length; i++) {
    const { item, time } = cached[i];
    if (!Number.isFinite(time)) continue;
    const open = Number(item?.[`${prefix}_open`]);
    const high = Number(item?.[`${prefix}_high`]);
    const low = Number(item?.[`${prefix}_low`]);
    const close = Number(item?.[`${prefix}_close`]);
    if (!Number.isFinite(open) || !Number.isFinite(high) || !Number.isFinite(low) || !Number.isFinite(close)) continue;
    result.push({ time, open, high, low, close });
  }
  return result;
}

function insertWhitespace(points, interval) {
  const step = INTERVAL_SECONDS[interval];
  if (!step || points.length < 2) {
    return points;
  }

  // Cap gap fill to prevent array explosion (e.g., 8h overnight gap = 480 empty 1T points)
  const maxGapPoints = 30;
  const expanded = [];

  for (let index = 0; index < points.length; index += 1) {
    const point = points[index];
    const nextPoint = points[index + 1];

    expanded.push(point);

    if (!nextPoint) {
      continue;
    }

    const gapSteps = Math.floor((nextPoint.time - point.time) / step) - 1;
    const fillCount = Math.min(gapSteps, maxGapPoints);

    for (let g = 1; g <= fillCount; g++) {
      expanded.push({ time: point.time + step * g });
    }
  }

  return expanded;
}

// TTL for the URL-based fetchCachedJson (short — deduplicates rapid requests)
function getHistoricalKlineCacheTtl(interval) {
  switch (interval) {
    case "1T":
      return 5000;
    case "15T":
      return 15000;
    case "1H":
      return 30000;
    case "4H":
      return 60000;
    case "1D":
      return 180000;
    default:
      return 10000;
  }
}

// TTL for kline history cache (long — WebSocket handles live updates)
function getKlineCacheTtl(interval) {
  switch (interval) {
    case "1T":
      return 120000;    // 2 minutes
    case "15T":
      return 300000;    // 5 minutes
    case "1H":
      return 600000;    // 10 minutes
    case "4H":
      return 1800000;   // 30 minutes
    case "1D":
      return 3600000;   // 1 hour
    default:
      return 120000;
  }
}

function makeKlineCacheKey(target, origin, asset, interval) {
  return `${target}:${origin}:${asset}:${interval}`;
}

function formatDateTimeForApi(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
}

function mergeHistoricalRows(existing, incoming) {
  const a = (existing || []).filter((item) => item?.datetime_now);
  const b = (incoming || []).filter((item) => item?.datetime_now);

  if (!b.length) return a;
  if (!a.length) return b;

  // Both arrays are already sorted by datetime_now — O(n) merge
  const result = [];
  let i = 0;
  let j = 0;

  while (i < a.length && j < b.length) {
    const cmp = a[i].datetime_now.localeCompare(b[j].datetime_now);
    if (cmp < 0) {
      result.push(a[i++]);
    } else if (cmp > 0) {
      result.push(b[j++]);
    } else {
      // Same timestamp — prefer existing (more recent data)
      result.push(a[i++]);
      j++;
    }
  }

  while (i < a.length) result.push(a[i++]);
  while (j < b.length) result.push(b[j++]);

  return result;
}

function extractExchange(marketCode) {
  return marketCode?.split("_")?.[0] || "";
}

function formatMarketLabel(marketCode) {
  if (!marketCode) {
    return "-";
  }

  const [marketName, quoteAsset] = marketCode.split("/");
  const parts = marketName.split("_");
  const exchange = parts[0];
  const marketType = parts.slice(1).join("_");

  const exchangeLabelMap = {
    UPBIT: "업비트",
    BITHUMB: "빗썸",
    COINONE: "코인원",
    BINANCE: "바이낸스",
    BYBIT: "바이비트",
    OKX: "OKX",
    GATE: "게이트",
    HYPERLIQUID: "하이퍼리퀴드",
  };

  const marketTypeLabelMap = {
    SPOT: "",
    USD_M: "USD-M",
    COIN_M: "COIN-M",
  };

  const exchangeLabel = exchangeLabelMap[exchange] || exchange;
  const marketTypeLabel = marketTypeLabelMap[marketType] ?? marketType.replaceAll("_", "-");

  if (!marketTypeLabel) {
    return exchangeLabel;
  }

  return `${exchangeLabel} ${marketTypeLabel}${quoteAsset ? `/${quoteAsset}` : ""}`;
}

function uniq(values) {
  return [...new Set((values || []).filter(Boolean))];
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

function FundingCountdownText({ fundingTime }) {
  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    const timer = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const text = formatFundingCountdown(fundingTime, nowMs);
  if (!text) return null;
  return <>{text}</>;
}

function Badge({ active, children }) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-1 sm:px-2 py-0.5 sm:py-1 text-[0.54rem] sm:text-[0.68rem] font-semibold ${
        active ? "bg-positive/20 text-positive" : "bg-surface-elevated text-ink-muted"
      }`}
    >
      {children}
    </span>
  );
}

function WalletNetworkRow({ leftLabel, leftIcon, leftDirection, leftNetworks, activeNetworks, arrow, rightLabel, rightIcon, rightDirection, rightNetworks }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex items-center gap-2">
        <ExchangeIcon exchange={leftIcon} size={14} />
        <span className="text-[0.68rem] sm:text-sm font-bold text-ink">
          {leftLabel}
          <span className="ml-0.5 text-[0.6rem] sm:text-[0.78rem] font-medium text-ink-muted">({leftDirection})</span>
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-1">
        {leftNetworks.length ? leftNetworks.map((network) => (
          <Badge key={`left-${leftDirection}-${network}`} active={activeNetworks.includes(network)}>
            {network}
          </Badge>
        )) : <Badge active={false}>-</Badge>}
      </div>
      <span className="mx-0.5 sm:mx-1 text-sm sm:text-lg font-bold text-positive">{arrow}</span>
      <div className="flex items-center gap-2">
        <ExchangeIcon exchange={rightIcon} size={14} />
        <span className="text-[0.68rem] sm:text-sm font-bold text-ink">
          {rightLabel}
          <span className="ml-0.5 text-[0.6rem] sm:text-[0.78rem] font-medium text-ink-muted">({rightDirection})</span>
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-1">
        {rightNetworks.length ? rightNetworks.map((network) => (
          <Badge key={`right-${rightDirection}-${network}`} active={activeNetworks.includes(network)}>
            {network}
          </Badge>
        )) : <Badge active={false}>-</Badge>}
      </div>
    </div>
  );
}

export default function PremiumChartPanel({
  asset,
  isTetherPriceView = false,
  originFunding,
  originMarketCode,
  row,
  targetFunding,
  targetMarketCode,
  walletNetworks = {},
}) {
  const chartContainerRef = useRef(null);
  const tooltipRef = useRef(null);
  const chartRef = useRef(null);
  const priceSeriesRef = useRef(null);
  const premiumSeriesRef = useRef(null);
  const lastLiveTimeRef = useRef(null);
  const chartDataLengthRef = useRef(0);
  const preserveLogicalRangeRef = useRef(null);
  const loadOlderHistoryRef = useRef(null);
  const isLoadingOlderRef = useRef(false);
  const hasOlderHistoryRef = useRef(true);
  const resetViewportRef = useRef(true);
  const initialViewportReadyRef = useRef(false);
  const initialViewportTimerRef = useRef(null);
  const loadingRef = useRef(true);
  const historyGenRef = useRef(0);
  const oldestDatetimeRef = useRef(null);
  const [interval, setChartInterval] = useState("1T");
  const [chartStyle, setChartStyle] = useState("ohlc");
  const [dataMode, setDataMode] = useState("premium");
  const [history, setHistory] = useState([]);
  const [liveRow, setLiveRow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [hasOlderHistory, setHasOlderHistory] = useState(true);
  const [error, setError] = useState("");
  const showTether = isTetherPriceView;

  useEffect(() => {
    hasOlderHistoryRef.current = hasOlderHistory;
  }, [hasOlderHistory]);

  useEffect(() => {
    loadingRef.current = loading;
  }, [loading]);

  useEffect(() => {
    oldestDatetimeRef.current = history[0]?.datetime_now || null;
  }, [history]);

  const fetchHistoricalChunk = useCallback(
    async ({ endTime, limit, signal }) => {
      const params = new URLSearchParams({
        target_market_code: targetMarketCode,
        origin_market_code: originMarketCode,
        base_asset: asset,
        interval,
        tz: getBrowserTimezone(),
        limit: String(limit),
      });

      if (endTime) {
        params.set("end_time", formatDateTimeForApi(endTime));
      }

      const payload = await fetchCachedJson(`/api/infocore/kline/?${params.toString()}`, {
        ttlMs: getHistoricalKlineCacheTtl(interval),
        fetchOptions: { signal },
      });

      return Array.isArray(payload) ? payload : [];
    },
    [asset, interval, originMarketCode, targetMarketCode],
  );

  useEffect(() => {
    let active = true;

    async function loadHistory() {
      if (!asset || !targetMarketCode || !originMarketCode) {
        return;
      }

      setError("");
      setHasOlderHistory(true);
      historyGenRef.current += 1;
      resetViewportRef.current = true;
      initialViewportReadyRef.current = false;
      preserveLogicalRangeRef.current = null;
      chartDataLengthRef.current = 0;
      if (initialViewportTimerRef.current) {
        window.clearTimeout(initialViewportTimerRef.current);
        initialViewportTimerRef.current = null;
      }

      // ── Stale-while-revalidate ──
      const cacheKey = makeKlineCacheKey(targetMarketCode, originMarketCode, asset, interval);
      const cached = getKlineCache(cacheKey);

      if (cached) {
        // Cache hit — show data immediately, no loading spinner
        setHistory(cached.data);
        setHasOlderHistory(cached.data.length >= HISTORY_INITIAL_LIMIT);
        setLoading(false);

        if (cached.fresh) {
          // Data is still fresh — skip network request
          return;
        }

        // Data is stale — fetch fresh in background (no loading spinner)
      } else {
        // Cache miss — show loading spinner
        setLoading(true);
      }

      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 8000);

      try {
        const payload = await fetchHistoricalChunk({
          limit: HISTORY_INITIAL_LIMIT,
          signal: controller.signal,
        });

        if (!active) {
          return;
        }

        setKlineCache(cacheKey, payload, getKlineCacheTtl(interval));
        setHistory(payload);
        setHasOlderHistory(payload.length >= HISTORY_INITIAL_LIMIT);
      } catch (requestError) {
        if (!active) {
          return;
        }
        // If we already showed cached data, don't clear it on network error
        if (!cached) {
          setHistory([]);
          setHasOlderHistory(false);
        }
        setError(
          requestError?.name === "AbortError"
            ? (cached ? "" : "차트 요청이 시간 초과되었습니다.")
            : (cached ? "" : (requestError.message || "차트 데이터를 불러오지 못했습니다."))
        );
      } finally {
        window.clearTimeout(timeoutId);
        if (active) {
          setLoading(false);
        }
      }
    }

    loadHistory();

    return () => {
      active = false;
      if (initialViewportTimerRef.current) {
        window.clearTimeout(initialViewportTimerRef.current);
        initialViewportTimerRef.current = null;
      }
    };
  }, [fetchHistoricalChunk]);

  const loadOlderHistory = useCallback(async () => {
    if (!asset || !targetMarketCode || !originMarketCode || isLoadingOlderRef.current || !hasOlderHistoryRef.current) {
      return;
    }

    const oldestDatetime = oldestDatetimeRef.current;
    if (!oldestDatetime) {
      return;
    }

    const gen = historyGenRef.current;
    isLoadingOlderRef.current = true;
    setLoadingOlder(true);

    try {
      const payload = await fetchHistoricalChunk({
        endTime: new Date(oldestDatetime),
        limit: HISTORY_OLDER_LIMIT,
      });

      // Discard if the asset/interval changed while loading
      if (gen !== historyGenRef.current) {
        return;
      }

      // Save viewport state before triggering React update
      if (chartRef.current) {
        const savedLogical = chartRef.current.timeScale().getVisibleLogicalRange();
        preserveLogicalRangeRef.current = {
          logical: savedLogical ? { from: savedLogical.from, to: savedLogical.to } : null,
          dataLength: chartDataLengthRef.current,
        };

        // Hide the chart canvas to prevent intermediate (wrong viewport) frame
        const container = chartContainerRef.current;
        if (container) {
          container.style.visibility = "hidden";
        }
      }

      setHistory((current) => {
        const merged = mergeHistoricalRows(current, payload);
        // Update kline cache with the expanded history
        const cacheKey = makeKlineCacheKey(targetMarketCode, originMarketCode, asset, interval);
        setKlineCache(cacheKey, merged, getKlineCacheTtl(interval));
        return merged;
      });
      setHasOlderHistory(payload.length >= HISTORY_OLDER_LIMIT);
    } catch {
      preserveLogicalRangeRef.current = null;
      if (chartContainerRef.current) {
        chartContainerRef.current.style.visibility = "";
      }
    } finally {
      isLoadingOlderRef.current = false;
      setLoadingOlder(false);
    }
  }, [asset, fetchHistoricalChunk, originMarketCode, targetMarketCode]);

  useEffect(() => {
    loadOlderHistoryRef.current = loadOlderHistory;
  }, [loadOlderHistory]);

  useEffect(() => {
    if (!asset || !targetMarketCode || !originMarketCode || !interval) {
      setLiveRow(null);
      return;
    }

    let active = true;
    let reconnectTimer = null;
    let socket = null;

    async function seedCurrentSnapshot() {
      try {
        const params = new URLSearchParams({
          target_market_code: targetMarketCode,
          origin_market_code: originMarketCode,
          base_asset: asset,
          interval,
        });
        const payload = await fetchCachedJson(`/api/infocore/kline-current/?${params.toString()}`, {
          ttlMs: 250,
        });
        if (!active) {
          return;
        }
        setLiveRow(Array.isArray(payload) ? payload[0] || null : null);
      } catch {
        if (active) {
          setLiveRow(null);
        }
      }
    }

    const wsBase = (
      process.env.NEXT_PUBLIC_DRF_WS_URL ||
      process.env.NEXT_PUBLIC_DRF_URL?.replace(/^http/i, "ws") ||
      window.location.origin.replace(/^http/i, "ws")
    ).replace(/\/$/, "");

    const url = new URL(`${wsBase}/kline/`);
    url.searchParams.set("target_market_code", targetMarketCode);
    url.searchParams.set("origin_market_code", originMarketCode);
    url.searchParams.set("interval", interval);
    url.searchParams.set("base_asset", asset);

    let reconnectAttempt = 0;

    const connect = () => {
      socket = new WebSocket(url.toString());

      socket.addEventListener("open", () => {
        reconnectAttempt = 0;
      });

      socket.addEventListener("message", (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type !== "publish") {
            return;
          }

          const payload = JSON.parse(message.result);
          if (!Array.isArray(payload) || !payload.length) {
            return;
          }

          if (active) {
            setLiveRow(payload[0] || null);
          }
        } catch {
          // Ignore malformed chart websocket payloads.
        }
      });

      socket.addEventListener("close", () => {
        if (!active) {
          return;
        }
        const delay = Math.min(1500 * Math.pow(2, reconnectAttempt), 30000);
        reconnectAttempt++;
        reconnectTimer = window.setTimeout(connect, delay);
      });
    };

    seedCurrentSnapshot();
    connect();

    return () => {
      active = false;
      if (reconnectTimer) {
        window.clearTimeout(reconnectTimer);
      }
      if (socket) {
        socket.close();
      }
    };
  }, [asset, interval, originMarketCode, targetMarketCode]);


  const chartPayload = useMemo(() => {
    // Pre-compute timestamps once — avoids repeated new Date() for each series
    const cached = precomputeTimestamps(history);

    const priceLine = {
      color: "#4a83ff",
      data: insertWhitespace(makeTimeSeries(cached, "tp"), interval),
    };

    let prefix, color, label;
    if (dataMode === "exit") {
      prefix = "SL"; color = "#4fd3a7"; label = "탈출김프";
    } else if (dataMode === "entry") {
      prefix = "LS"; color = "#16c784"; label = "진입김프";
    } else {
      // "premium" — true premium based on last price (tp_*)
      prefix = "tp"; color = "#f0b90b"; label = "김프";
    }

    return {
      priceLine,
      candlestickData: insertWhitespace(makeCandlestickSeries(cached, prefix), interval),
      legend: [
        { color: "#4a83ff", label: "현재가" },
        { color, label },
      ],
      premiumLines: [
        {
          color,
          data: insertWhitespace(makeTimeSeries(cached, `${prefix}_close`), interval),
          label,
        },
      ],
    };
  }, [dataMode, history, interval]);

  const liveChartPoint = useMemo(() => {
    if (!liveRow?.datetime_now) {
      return null;
    }

    const dateValue = new Date(liveRow.datetime_now).getTime();
    if (!Number.isFinite(dateValue)) {
      return null;
    }

    const prefix = dataMode === "exit" ? "SL" : dataMode === "entry" ? "LS" : "tp";
    const open = Number(liveRow?.[`${prefix}_open`]);
    const high = Number(liveRow?.[`${prefix}_high`]);
    const low = Number(liveRow?.[`${prefix}_low`]);
    const close = Number(liveRow?.[`${prefix}_close`]);
    const tp = Number(liveRow?.tp);
    const dollar = Number(liveRow?.dollar);
    const time = toLocalChartTime(dateValue);

    if (
      !Number.isFinite(open) ||
      !Number.isFinite(high) ||
      !Number.isFinite(low) ||
      !Number.isFinite(close)
    ) {
      return null;
    }

    if (showTether && Number.isFinite(dollar)) {
      return {
        candlestick: {
          time,
          open: dollar * (1 + open * 0.01),
          high: dollar * (1 + high * 0.01),
          low: dollar * (1 + low * 0.01),
          close: dollar * (1 + close * 0.01),
        },
        premiumLine: {
          time,
          value: dollar * (1 + close * 0.01),
        },
        priceLine: Number.isFinite(tp) ? { time, value: tp } : null,
      };
    }

    return {
      candlestick: { time, open, high, low, close },
      premiumLine: { time, value: close },
      priceLine: Number.isFinite(tp) ? { time, value: tp } : null,
    };
  }, [dataMode, liveRow, showTether]);

  useEffect(() => {
    const container = chartContainerRef.current;

    if (!container) {
      return undefined;
    }

    const chart = createChart(container, {
      autoSize: true,
      height: 340,
      layout: {
        background: { color: "transparent" },
        textColor: "#8f9bb7",
        fontSize: 11,
      },
      grid: {
        horzLines: { color: "rgba(92, 113, 153, 0.12)" },
        vertLines: { color: "rgba(92, 113, 153, 0.06)" },
      },
      leftPriceScale: {
        visible: true,
        borderColor: "rgba(92, 113, 153, 0.15)",
      },
      rightPriceScale: {
        borderColor: "rgba(92, 113, 153, 0.15)",
      },
      timeScale: {
        borderColor: "rgba(92, 113, 153, 0.15)",
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 12,
        rightBarStaysOnScroll: true,
        shiftVisibleRangeOnNewBar: true,
      },
      crosshair: {
        horzLine: { color: "rgba(99, 132, 255, 0.3)", style: 2 },
        vertLine: { color: "rgba(99, 132, 255, 0.2)", style: 2 },
      },
    });

    const seriesRefs = [];

    // Price line — always a line on the left Y-axis
    const priceSeries = chart.addSeries(LineSeries, {
      color: "#4a83ff",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
      priceScaleId: "left",
      priceFormat: {
        type: "custom",
        formatter: (price) => formatCompactPrice(price),
        minMove: 1,
      },
    });
    priceSeries.setData([]);
    priceSeriesRef.current = priceSeries;
    seriesRefs.push(priceSeries);

    // Premium series on right Y-axis
    let premiumSeries = null;
    if (chartStyle === "ohlc") {
      premiumSeries = chart.addSeries(CandlestickSeries, {
        upColor: "#16c784",
        downColor: "#ea3943",
        borderVisible: false,
        wickUpColor: "#16c784",
        wickDownColor: "#ea3943",
        priceLineVisible: false,
        lastValueVisible: true,
        priceScaleId: "right",
        priceFormat: { type: "price", precision: 3, minMove: 0.001 },
      });
      premiumSeries.setData([]);
      seriesRefs.push(premiumSeries);
    } else {
      const lineSeries = chart.addSeries(LineSeries, {
        color: "#16c784",
        lineWidth: 2,
        priceLineVisible: false,
        lastValueVisible: true,
        priceScaleId: "right",
        priceFormat: { type: "price", precision: 3, minMove: 0.001 },
      });
      lineSeries.setData([]);
      seriesRefs.push(lineSeries);
      premiumSeries = lineSeries;
    }
    premiumSeriesRef.current = premiumSeries;
    chartRef.current = chart;

    // Crosshair tooltip
    const tooltip = tooltipRef.current;
    chart.subscribeCrosshairMove((param) => {
      if (!tooltip) return;

      if (!param.time || !param.point || param.point.x < 0 || param.point.y < 0) {
        tooltip.style.display = "none";
        return;
      }

      const priceData = param.seriesData.get(priceSeries);
      const premiumData = premiumSeries ? param.seriesData.get(premiumSeries) : null;

      const priceValue = priceData?.value ?? priceData?.close;
      const premiumValue = premiumData?.value ?? premiumData?.close;

      if (priceValue === undefined && premiumValue === undefined) {
        tooltip.style.display = "none";
        return;
      }

      const lines = [];
      if (priceValue !== undefined) {
        lines.push(`<span style="color:#4a83ff">가격</span> <strong>${formatNumber(priceValue, 1)}</strong>`);
      }
      if (premiumValue !== undefined) {
        lines.push(`<span style="color:#16c784">프리미엄</span> <strong>${premiumValue.toFixed(3)}%</strong>`);
      }

      tooltip.innerHTML = lines.join("<br>");
      tooltip.style.display = "block";

      const chartRect = container.getBoundingClientRect();
      const tooltipWidth = tooltip.offsetWidth;
      let left = param.point.x + 12;
      if (left + tooltipWidth > chartRect.width) {
        left = param.point.x - tooltipWidth - 12;
      }

      tooltip.style.left = `${left}px`;
      tooltip.style.top = `${param.point.y - 12}px`;
    });

    chart.timeScale().subscribeVisibleLogicalRangeChange((visibleRange) => {
      if (
        !visibleRange ||
        !priceSeriesRef.current ||
        !loadOlderHistoryRef.current ||
        resetViewportRef.current ||
        !initialViewportReadyRef.current ||
        chartDataLengthRef.current === 0 ||
        loadingRef.current
      ) {
        return;
      }

      if ((visibleRange.from ?? Number.POSITIVE_INFINITY) > HISTORY_LOAD_THRESHOLD) {
        return;
      }

      loadOlderHistoryRef.current();
    });

    return () => {
      if (initialViewportTimerRef.current) {
        window.clearTimeout(initialViewportTimerRef.current);
        initialViewportTimerRef.current = null;
      }
      seriesRefs.forEach((series) => {
        chart.removeSeries(series);
      });
      chartRef.current = null;
      priceSeriesRef.current = null;
      premiumSeriesRef.current = null;
      lastLiveTimeRef.current = null;
      chart.remove();
    };
  }, [chartStyle]);

  useEffect(() => {
    if (!chartRef.current || !priceSeriesRef.current || !premiumSeriesRef.current) {
      return;
    }

    const nextLength =
      chartStyle === "ohlc"
        ? chartPayload.candlestickData.length
        : (chartPayload.premiumLines[0]?.data?.length || 0);

    const currentLastPoint =
      chartPayload.priceLine.data.length
        ? chartPayload.priceLine.data[chartPayload.priceLine.data.length - 1]
        : null;

    priceSeriesRef.current.applyOptions({
      color: chartPayload.priceLine.color,
    });
    priceSeriesRef.current.setData(chartPayload.priceLine.data);

    if (chartStyle === "ohlc") {
      premiumSeriesRef.current.setData(chartPayload.candlestickData);
    } else {
      premiumSeriesRef.current.applyOptions({
        color: chartPayload.premiumLines[0]?.color || "#16c784",
      });
      premiumSeriesRef.current.setData(chartPayload.premiumLines[0]?.data || []);
    }

    lastLiveTimeRef.current = currentLastPoint?.time ?? null;

    if (preserveLogicalRangeRef.current?.logical) {
      const { logical, dataLength } = preserveLogicalRangeRef.current;
      const shift = nextLength - (dataLength || 0);
      preserveLogicalRangeRef.current = null;

      if (Number.isFinite(shift) && shift > 0 && logical) {
        const restored = { from: logical.from + shift, to: logical.to + shift };

        // Apply viewport restoration in rAF — chart needs one frame to process setData
        window.requestAnimationFrame(() => {
          chartRef.current?.timeScale().setVisibleLogicalRange(restored);

          // Show the chart canvas again after viewport is restored
          if (chartContainerRef.current) {
            chartContainerRef.current.style.visibility = "";
          }
        });
      } else {
        // No shift needed — just show chart
        if (chartContainerRef.current) {
          chartContainerRef.current.style.visibility = "";
        }
      }
    } else if (resetViewportRef.current && !loading) {
      window.requestAnimationFrame(() => {
        const applyInitialViewport = () => {
          const to = Math.max(nextLength - 1 + INITIAL_RIGHT_OFFSET_BARS, INITIAL_VISIBLE_BARS);
          const from = Math.max(0, to - INITIAL_VISIBLE_BARS);
          chartRef.current?.timeScale().setVisibleLogicalRange({ from, to });
          chartRef.current?.timeScale().scrollToPosition(INITIAL_RIGHT_OFFSET_BARS, false);
        };

        applyInitialViewport();
        initialViewportTimerRef.current = window.setTimeout(() => {
          applyInitialViewport();
          initialViewportReadyRef.current = true;
          initialViewportTimerRef.current = null;
        }, 120);
      });
      resetViewportRef.current = false;
    }

    chartDataLengthRef.current = nextLength;
  }, [chartPayload, chartStyle, loading]);

  useEffect(() => {
    if (!liveChartPoint || !priceSeriesRef.current || !premiumSeriesRef.current) {
      return;
    }

    if (
      lastLiveTimeRef.current !== null &&
      Number.isFinite(lastLiveTimeRef.current) &&
      liveChartPoint.priceLine &&
      liveChartPoint.priceLine.time < lastLiveTimeRef.current
    ) {
      return;
    }

    if (liveChartPoint.priceLine) {
      priceSeriesRef.current.update(liveChartPoint.priceLine);
      lastLiveTimeRef.current = liveChartPoint.priceLine.time;
    }

    if (chartStyle === "ohlc") {
      premiumSeriesRef.current.update(liveChartPoint.candlestick);
      return;
    }

    premiumSeriesRef.current.update(liveChartPoint.premiumLine);
  }, [chartStyle, liveChartPoint]);

  const spread = Number(row?.SL_close || 0) - Number(row?.LS_close || 0);
  const targetExchange = extractExchange(targetMarketCode);
  const originExchange = extractExchange(originMarketCode);
  const targetLabel = formatMarketLabel(targetMarketCode);
  const originLabel = formatMarketLabel(originMarketCode);
  const { targetDeposit, targetWithdraw, originDeposit, originWithdraw } = useMemo(() => ({
    targetDeposit: uniq(walletNetworks?.[targetExchange]?.deposit || []),
    targetWithdraw: uniq(walletNetworks?.[targetExchange]?.withdraw || []),
    originDeposit: uniq(walletNetworks?.[originExchange]?.deposit || []),
    originWithdraw: uniq(walletNetworks?.[originExchange]?.withdraw || []),
  }), [walletNetworks, targetExchange, originExchange]);
  // Compute active networks: right = target withdraw ∩ origin deposit, left = origin withdraw ∩ target deposit
  const walletStatusSummary = useMemo(() => {
    const right = targetWithdraw.filter((n) => originDeposit.includes(n));
    const left = originWithdraw.filter((n) => targetDeposit.includes(n));
    return { right, left, all: [...new Set([...right, ...left])] };
  }, [targetWithdraw, originDeposit, originWithdraw, targetDeposit]);
  const hasTargetFundingTime = !!targetFunding?.funding_time;
  const hasOriginFundingTime = !!originFunding?.funding_time;

  return (
    <div
      className="rounded-lg border border-border bg-background/95 overflow-hidden"
      style={{ animation: "riseIn 350ms cubic-bezier(0.4, 0, 0.15, 1) both" }}
    >
      {/* Binance-style toolbar */}
      <div className="flex flex-wrap items-center gap-x-2 sm:gap-x-4 gap-y-1 border-b border-border/50 px-2 sm:px-3 py-1.5 sm:py-2">
        {/* Asset + key stats */}
        <h3 className="text-xs sm:text-sm font-bold text-ink">{asset}</h3>
        <div className="flex items-center gap-1.5 sm:gap-3 text-[0.58rem] sm:text-[0.7rem] text-ink-muted">
          <span>현재가 <strong className="text-ink">{formatNumber(row?.tp, 1)}</strong></span>
          <span>스프레드 <strong className={spread > 0 ? "text-positive" : spread < 0 ? "text-negative" : "text-ink"}>{formatNumber(spread, 3)}%p</strong></span>
          <span>
            펀딩{" "}
            <strong className={polarityColor(targetFunding?.funding_rate)}>
              {formatFundingPercent(targetFunding?.funding_rate)}
            </strong>
            {targetFunding?.funding_interval_hours ? (
              <span className={`ml-1 rounded px-1.5 py-0.5 text-[10px] font-bold leading-none ${fundingBadgeClass(targetFunding.funding_interval_hours)}`}>
                {targetFunding.funding_interval_hours}h
              </span>
            ) : null}
            {" / "}
            <strong className={polarityColor(originFunding?.funding_rate)}>
              {formatFundingPercent(originFunding?.funding_rate)}
            </strong>
            {originFunding?.funding_interval_hours ? (
              <span className={`ml-1 rounded px-1.5 py-0.5 text-[10px] font-bold leading-none ${fundingBadgeClass(originFunding.funding_interval_hours)}`}>
                {originFunding.funding_interval_hours}h
              </span>
            ) : null}
          </span>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Legend dots */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 text-[0.54rem] sm:text-[0.66rem] text-ink-muted">
          {chartPayload.legend.map((item) => (
            <span key={item.label} className="flex items-center gap-1">
              <span className="inline-block h-2 w-2 rounded-full" style={{ background: item.color }} />
              {item.label}
            </span>
          ))}
        </div>
      </div>

      <div className="grid gap-1 sm:gap-2 border-b border-border/50 bg-surface-elevated/10 px-2 sm:px-3 py-2 sm:py-3">
        {(hasTargetFundingTime || hasOriginFundingTime) ? (
          <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-[0.58rem] sm:text-[0.72rem] italic text-ink-muted">
            {hasTargetFundingTime ? (
              <span>{targetLabel} 펀딩까지 <FundingCountdownText fundingTime={targetFunding.funding_time} /></span>
            ) : null}
            {hasOriginFundingTime ? (
              <span>{originLabel} 펀딩까지 <FundingCountdownText fundingTime={originFunding.funding_time} /></span>
            ) : null}
          </div>
        ) : null}
        <WalletNetworkRow
          leftDirection="출금"
          leftIcon={targetExchange}
          leftLabel={targetLabel}
          leftNetworks={targetWithdraw}
          activeNetworks={walletStatusSummary.right}
          arrow="→"
          rightDirection="입금"
          rightIcon={originExchange}
          rightLabel={originLabel}
          rightNetworks={originDeposit}
        />
        <WalletNetworkRow
          leftDirection="입금"
          leftIcon={targetExchange}
          leftLabel={targetLabel}
          leftNetworks={targetDeposit}
          activeNetworks={walletStatusSummary.left}
          arrow="←"
          rightDirection="출금"
          rightIcon={originExchange}
          rightLabel={originLabel}
          rightNetworks={originWithdraw}
        />
      </div>

      {/* Interval bar + data mode + chart type — inside the chart area */}
      <div className="flex flex-wrap items-center gap-1 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 bg-surface-elevated/20">
        {/* Intervals */}
        <div className="flex items-center gap-0.5">
          {INTERVALS.map((opt) => (
            <button
              key={opt.value}
              className={`rounded px-1.5 sm:px-2 py-px sm:py-0.5 text-[0.56rem] sm:text-[0.68rem] font-bold transition-colors ${
                interval === opt.value
                  ? "bg-accent/15 text-accent"
                  : "text-ink-muted hover:text-ink hover:bg-surface-elevated/60"
              }`}
              onClick={() => setChartInterval(opt.value)}
              type="button"
            >
              {opt.label}
            </button>
          ))}
        </div>

        {/* Separator */}
        <div className="h-4 w-px bg-border/50" />

        {/* Data mode: 김프 / 진입 / 탈출 */}
        <div className="flex items-center gap-0.5">
          {DATA_MODES.map((opt) => (
            <button
              key={opt.value}
              className={`rounded px-1.5 sm:px-2 py-px sm:py-0.5 text-[0.56rem] sm:text-[0.68rem] font-bold transition-colors ${
                dataMode === opt.value
                  ? "bg-accent/15 text-accent"
                  : "text-ink-muted hover:text-ink hover:bg-surface-elevated/60"
              }`}
              onClick={() => setDataMode(opt.value)}
              type="button"
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="flex-1" />

        {/* Chart style icons */}
        <div className="flex items-center rounded-md border border-border/50 bg-background/70 p-0.5">
          <button
            className={`rounded p-1 transition-colors ${
              chartStyle === "ohlc"
                ? "bg-accent/15 text-accent"
                : "text-ink-muted hover:text-ink"
            }`}
            onClick={() => setChartStyle("ohlc")}
            title="캔들 차트"
            type="button"
          >
            <ChartCandlestick size={14} strokeWidth={2} />
          </button>
          <button
            className={`rounded p-1 transition-colors ${
              chartStyle === "line"
                ? "bg-accent/15 text-accent"
                : "text-ink-muted hover:text-ink"
            }`}
            onClick={() => setChartStyle("line")}
            title="꺾은선 차트"
            type="button"
          >
            <ChartLine size={14} strokeWidth={2} />
          </button>
        </div>
      </div>

      {/* Chart canvas */}
      <div className="relative" style={{ minHeight: 340 }}>
        {loading ? (
          <div className="absolute inset-0 grid place-items-center text-sm text-ink-muted">
            <div className="flex items-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-border border-t-accent" />
              차트 로딩 중...
            </div>
          </div>
        ) : null}
        {!loading && error ? (
          <div className="absolute inset-0 grid place-items-center text-sm text-ink-muted">
            {error}
          </div>
        ) : null}
        <div className="relative h-[260px] sm:h-[340px]">
          {/* Axis labels */}
          <div className="pointer-events-none absolute top-1 left-1 z-10 rounded bg-background/80 px-1.5 py-0.5 text-[0.6rem] font-bold text-[#4a83ff]">
            가격
          </div>
          <div className="pointer-events-none absolute top-1 right-1 z-10 rounded bg-background/80 px-1.5 py-0.5 text-[0.6rem] font-bold text-[#16c784]">
            프리미엄 %
          </div>
          {/* Crosshair tooltip */}
          <div
            ref={tooltipRef}
            className="pointer-events-none absolute z-20 hidden rounded border border-border/60 bg-background/90 px-2 py-1.5 text-[0.68rem] leading-relaxed text-ink backdrop-blur-sm"
            style={{ whiteSpace: "nowrap" }}
          />
          {loadingOlder ? (
            <div className="pointer-events-none absolute left-3 top-8 z-10 rounded border border-border/60 bg-background/90 px-2 py-1 text-[0.65rem] text-ink-muted backdrop-blur-sm">
              과거 봉 로딩 중...
            </div>
          ) : null}
          <div ref={chartContainerRef} className="h-full w-full" />
        </div>
      </div>
    </div>
  );
}
