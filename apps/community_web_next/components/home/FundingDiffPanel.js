"use client";

function formatPercent(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return `${Number(value).toFixed(4)}%`;
}

function polarityColor(value) {
  const n = Number(value || 0);
  if (n > 0) return "text-positive";
  if (n < 0) return "text-negative";
  return "text-ink-muted";
}

function SkeletonRows() {
  return Array.from({ length: 5 }).map((_, i) => (
    <tr key={i}>
      {Array.from({ length: 4 }).map((_, j) => (
        <td key={j} className="px-3 py-2.5">
          <div className="h-3 rounded bg-gradient-to-r from-border/20 via-border/40 to-border/20 bg-[length:200%_100%] animate-[shimmer_1.4s_linear_infinite]" />
        </td>
      ))}
    </tr>
  ));
}

export default function FundingDiffPanel({ fundingDiff = [], loading = false }) {
  return (
    <section className="rounded-lg border border-border bg-background/92 p-4">
      <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-ink">
        <span className="h-3.5 w-0.5 rounded-full bg-accent" />
        펀딩비 차이
      </h2>
      <div className="overflow-x-auto rounded-lg border border-border bg-background/90">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border">
              <th className="px-3 py-2 text-left text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">자산</th>
              <th className="px-3 py-2 text-right text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">타겟 펀딩</th>
              <th className="px-3 py-2 text-right text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">오리진 펀딩</th>
              <th className="px-3 py-2 text-right text-[0.62rem] font-bold uppercase tracking-widest text-ink-muted">차이</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <SkeletonRows />
            ) : fundingDiff.length ? (
              fundingDiff.map((item, index) => (
                <tr key={`${item.base_asset}-${index}`} className="border-t border-border/50 transition-colors hover:bg-surface-elevated/30">
                  <td className="px-3 py-2 text-sm font-semibold text-ink">{item.base_asset}</td>
                  <td className={`tabular-nums px-3 py-2 text-right font-mono text-sm ${polarityColor(item.funding_rate_x)}`}>
                    {formatPercent(item.funding_rate_x)}
                  </td>
                  <td className={`tabular-nums px-3 py-2 text-right font-mono text-sm ${polarityColor(item.funding_rate_y)}`}>
                    {formatPercent(item.funding_rate_y)}
                  </td>
                  <td className={`tabular-nums px-3 py-2 text-right font-mono text-sm font-semibold ${polarityColor(item.funding_rate_diff)}`}>
                    {formatPercent(item.funding_rate_diff)}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" className="px-4 py-8 text-center">
                  <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-surface-elevated/40">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-ink-muted/40"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                  </div>
                  <p className="text-[0.78rem] text-ink-muted">펀딩비 데이터가 아직 없습니다.</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
