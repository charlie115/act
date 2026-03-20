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
          <div className="h-3 animate-pulse rounded bg-border/30" />
        </td>
      ))}
    </tr>
  ));
}

export default function FundingDiffPanel({ fundingDiff = [], loading = false }) {
  return (
    <section className="rounded-lg border border-border/60 bg-background/80 backdrop-blur-sm p-4 shadow-[0_0_30px_-10px_rgba(43,115,255,0.06)]">
      <h2 className="section-title mb-3">펀딩비 차이</h2>
      <div className="overflow-x-auto rounded-lg border border-border bg-background/90">
        <table className="w-full min-w-[480px] border-collapse">
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
                  <td className={`tabular-nums px-3 py-2 text-right text-sm ${polarityColor(item.funding_rate_x)}`}>
                    {formatPercent(item.funding_rate_x)}
                  </td>
                  <td className={`tabular-nums px-3 py-2 text-right text-sm ${polarityColor(item.funding_rate_y)}`}>
                    {formatPercent(item.funding_rate_y)}
                  </td>
                  <td className={`tabular-nums px-3 py-2 text-right text-sm font-semibold ${polarityColor(item.funding_rate_diff)}`}>
                    {formatPercent(item.funding_rate_diff)}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4" className="px-4 py-8 text-center text-sm text-ink-muted">
                  표시할 펀딩 차이 데이터가 없습니다.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
