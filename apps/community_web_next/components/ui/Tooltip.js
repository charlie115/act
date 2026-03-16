"use client";

export default function Tooltip({ children, text }) {
  return (
    <span className="group relative inline-flex items-center">
      {children}
      <span className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-2 -translate-x-1/2 whitespace-nowrap rounded-lg border border-border bg-surface-elevated px-3 py-1.5 text-xs text-ink-muted opacity-0 shadow-lg transition-opacity group-hover:opacity-100">
        {text}
        <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-surface-elevated" />
      </span>
    </span>
  );
}
