import Image from "next/image";

const EXCHANGE_ICONS = {
  UPBIT: "/images/exchanges/upbit.svg",
  BITHUMB: "/images/exchanges/bithumb.svg",
  COINONE: "/images/exchanges/coinone.svg",
  BINANCE: "/images/exchanges/binance.svg",
  BYBIT: "/images/exchanges/bybit.svg",
  OKX: "/images/exchanges/okx.svg",
  GATE: "/images/exchanges/gate.svg",
  HYPERLIQUID: "/images/exchanges/hyperliquid.svg",
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

export default function ExchangeIcon({ exchange, size = 20 }) {
  const key = exchange?.toUpperCase() || "";
  const src = EXCHANGE_ICONS[key];

  if (!src) {
    const short = EXCHANGE_SHORT[key] || key.slice(0, 2);
    return (
      <span
        className="inline-flex items-center justify-center rounded-md bg-ink-muted/20 font-bold text-ink"
        style={{ width: size, height: size, fontSize: size * 0.45 }}
      >
        {short}
      </span>
    );
  }

  return (
    <Image
      alt={exchange}
      className="inline-block flex-shrink-0 rounded-md"
      height={size}
      src={src}
      width={size}
    />
  );
}
