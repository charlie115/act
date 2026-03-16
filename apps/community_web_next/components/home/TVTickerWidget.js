"use client";

import { useEffect, useRef } from "react";
import { TRADING_VIEW_TICKER_SYMBOLS } from "../../lib/constants";

const TICKER_CONFIG = {
  isTransparent: true,
  showSymbolLogo: true,
  autosize: true,
  colorTheme: "dark",
  locale: "kr",
  symbols: TRADING_VIEW_TICKER_SYMBOLS,
};

export default function TVTickerWidget() {
  const containerRef = useRef(null);
  const scriptLoadedRef = useRef(false);

  useEffect(() => {
    const container = containerRef.current;

    if (!container || scriptLoadedRef.current) {
      return;
    }

    scriptLoadedRef.current = true;

    const widgetDiv = document.createElement("div");
    widgetDiv.className = "tradingview-widget-container__widget";
    container.appendChild(widgetDiv);

    const script = document.createElement("script");
    script.type = "text/javascript";
    script.src =
      "https://s3.tradingview.com/external-embedding/embed-widget-ticker-tape.js";
    script.async = true;
    script.textContent = JSON.stringify(TICKER_CONFIG);
    container.appendChild(script);
  }, []);

  return (
    <div className="mx-auto w-[min(1280px,calc(100vw-20px))] overflow-hidden rounded-lg border border-border bg-background/80">
      <div ref={containerRef} className="tradingview-widget-container" />
    </div>
  );
}
