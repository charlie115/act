"use client";

const VARIANT_STYLES = {
  error: "border-negative/30 bg-negative/8 text-negative",
  info: "border-accent/20 bg-accent/5 text-accent",
  loading: "border-border bg-surface-elevated/30 text-ink-muted",
};

export default function SurfaceNotice({
  actions = null,
  className = "",
  description,
  onRetry,
  title,
  variant = "info",
}) {
  const variantStyle = VARIANT_STYLES[variant] || VARIANT_STYLES.info;

  return (
    <div className={`flex items-start justify-between gap-3 rounded-lg border px-3.5 py-2.5 text-sm ${variantStyle} ${className}`.trim()}>
      <div>
        {title ? <strong className="block text-[0.78rem] font-bold">{title}</strong> : null}
        {description ? <p className="text-[0.76rem] leading-relaxed opacity-90">{description}</p> : null}
      </div>
      {onRetry ? (
        <button
          className="shrink-0 rounded-md border border-current/20 bg-current/5 px-2.5 py-1 text-[0.72rem] font-semibold transition-colors hover:bg-current/10"
          onClick={onRetry}
          type="button"
        >
          재시도
        </button>
      ) : null}
      {actions ? <div className="shrink-0">{actions}</div> : null}
    </div>
  );
}
