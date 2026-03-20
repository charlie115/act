"use client";

import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef, useState } from "react";
import { ArrowLeftRight, ChevronDown, X } from "lucide-react";

function OptionRow({ item, selected, onSelect, tradeSupportRequired }) {
  const disabled =
    item.disabled || (tradeSupportRequired && item.value !== "ALL" && !item.tradeSupport);

  return (
    <button
      className={`flex w-full items-center justify-between gap-2 border-l-2 px-4 py-3 text-left text-sm transition-all ${
        disabled
          ? "pointer-events-none opacity-40 border-l-transparent"
          : selected
            ? "border-l-accent bg-accent/10 text-ink"
            : "border-l-transparent text-ink-muted hover:bg-surface-elevated/40 hover:text-ink"
      }`}
      disabled={disabled}
      onClick={() => onSelect(item)}
      type="button"
    >
      {item.target && item.origin ? (
        <span className="flex items-center gap-2 flex-wrap">
          <span>{item.target.getLabel()}</span>
          <ArrowLeftRight size={14} className="text-accent/60" />
          <span>{item.origin.getLabel()}</span>
        </span>
      ) : (
        <span>{item.getLabel?.() || item.label || item.value}</span>
      )}

      <span className="flex items-center gap-2 flex-shrink-0">
        {item.value !== "ALL" && item.tradeSupport ? (
          <span className="rounded-full bg-positive/15 px-2 py-0.5 text-[0.62rem] font-bold text-positive">Trade</span>
        ) : null}
        {selected && <span className="text-accent">✓</span>}
        {item.secondaryIcon || null}
      </span>
    </button>
  );
}

const BotMarketCodeCombinationSelector = forwardRef(function BotMarketCodeCombinationSelector(
  {
    buttonStyle,
    marketCodesRequired,
    onSelectItem,
    options = [],
    tradeSupportRequired,
    value,
  },
  ref
) {
  const [open, setOpen] = useState(false);
  const dialogRef = useRef(null);

  useImperativeHandle(ref, () => ({
    open: () => setOpen(true),
    toggle: () => setOpen((current) => !current),
  }));

  // Close on click outside
  useEffect(() => {
    if (!open) return;
    function handleClick(e) {
      if (dialogRef.current && !dialogRef.current.contains(e.target)) setOpen(false);
    }
    function handleKey(e) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handleClick);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  const buttonLabel = useMemo(() => {
    if (value?.target && value?.origin) {
      return `${value.target.getLabel()} ↔ ${value.origin.getLabel()}`;
    }

    return value?.getLabel?.() || value?.label || "마켓 조합 선택";
  }, [value]);

  function handleSelect(item) {
    if (item.disabled) {
      return;
    }

    onSelectItem?.(item);
    if (marketCodesRequired && item.value === "ALL") {
      return;
    }
    setOpen(false);
  }

  return (
    <div>
      <button
        className="flex w-full items-center justify-between gap-2 rounded-lg border border-border bg-background/80 px-3 py-2 text-[0.72rem] sm:text-sm text-ink transition-colors hover:border-accent/30"
        onClick={() => setOpen(true)}
        style={buttonStyle}
        type="button"
      >
        <span className="truncate">{buttonLabel}</span>
        <ChevronDown size={14} className="text-ink-muted flex-shrink-0" />
      </button>

      {open ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-black/50 backdrop-blur-sm p-4">
          <div
            ref={dialogRef}
            className="w-full max-w-md rounded-xl border border-border bg-background shadow-2xl"
            style={{ animation: "fadeSlideUp 0.2s cubic-bezier(0.16, 1, 0.3, 1)" }}
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <h3 className="text-sm font-bold text-ink">마켓 조합 선택</h3>
              <button
                className="rounded-lg p-1 text-ink-muted hover:bg-surface-elevated hover:text-ink cursor-pointer"
                onClick={() => setOpen(false)}
                type="button"
              >
                <X size={16} />
              </button>
            </div>
            <div className="max-h-[60vh] overflow-y-auto divide-y divide-border/30">
              {options.map((item) => (
                <OptionRow
                  item={item}
                  key={item.value}
                  onSelect={handleSelect}
                  selected={item.value === value?.value}
                  tradeSupportRequired={tradeSupportRequired}
                />
              ))}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
});

export default BotMarketCodeCombinationSelector;
