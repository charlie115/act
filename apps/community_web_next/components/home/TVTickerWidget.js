"use client";

import { memo, useEffect, useRef } from "react";

const TICKER_CONFIG = {
  isTransparent: true,
  showSymbolLogo: true,
  autosize: true,
  colorTheme: "dark",
  locale: "kr",
  symbols: [
    { proName: "FX_IDC:USDKRW", description: "달러" },
    { proName: "USDTKRW", description: "테더" },
    { proName: "CRYPTOCAP:BTC.D", description: "BTC도미넌스" },
    { proName: "BINANCE:BTCUSDT", description: "비트코인" },
    { proName: "FOREXCOM:NSXUSD", description: "나스닥" },
  ],
};

const TVTickerWidget = memo(function TVTickerWidget() {
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
    <div className="overflow-hidden" style={{ minHeight: 44 }}>
      <div ref={containerRef} className="tradingview-widget-container" />
    </div>
  );
});

export default TVTickerWidget;
