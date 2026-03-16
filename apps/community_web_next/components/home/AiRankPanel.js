"use client";

function SkeletonCards() {
  return Array.from({ length: 3 }).map((_, i) => (
    <div key={i} className="rounded-lg border border-border bg-background/70 p-3">
      <div className="mb-2 flex gap-2">
        <div className="h-3 w-16 animate-pulse rounded bg-border/30" />
        <div className="h-3 w-12 animate-pulse rounded bg-border/30" />
      </div>
      <div className="h-4 w-20 animate-pulse rounded bg-border/40" />
      <div className="mt-2 h-3 w-full animate-pulse rounded bg-border/20" />
    </div>
  ));
}

const RISK_LABELS = ["", "매우 낮음", "낮음", "보통", "높음", "매우 높음"];

export default function AiRankPanel({ recommendations = [], loading = false }) {
  return (
    <section className="rounded-lg border border-border bg-background/92 p-4">
      <h2 className="mb-3 flex items-center gap-2 text-sm font-bold text-ink">
        <span className="h-3.5 w-0.5 rounded-full bg-accent" />
        추천 자산
      </h2>
      <div className="grid gap-3">
        {loading ? (
          <SkeletonCards />
        ) : recommendations.length ? (
          recommendations.map((item) => (
            <article
              key={`${item.base_asset}-${item.rank}`}
              className="rounded-lg border-l-2 border-l-accent border border-border bg-background/70 p-3 transition-colors hover:bg-surface-elevated/30"
            >
              <div className="mb-1 flex flex-wrap gap-2 text-[0.68rem] text-ink-muted">
                <span className="font-bold tabular-nums text-accent">#{item.rank}</span>
                <span className={`rounded px-1.5 py-0.5 text-[0.6rem] font-bold ${
                  item.risk_level <= 2 ? "bg-positive/15 text-positive" :
                  item.risk_level <= 4 ? "bg-opportunity/15 text-opportunity" :
                  "bg-negative/15 text-negative"
                }`}>
                  위험 {RISK_LABELS[item.risk_level] || item.risk_level}
                </span>
              </div>
              <h3 className="text-sm font-bold text-ink">{item.base_asset}</h3>
              {item.ai_label ? (
                <span className="mt-1 inline-block rounded-full bg-accent/10 px-2 py-0.5 text-[0.64rem] font-semibold text-accent">
                  {item.ai_label}
                </span>
              ) : null}
              <p className="mt-1 text-[0.78rem] leading-relaxed text-ink-muted">{item.explanation}</p>
            </article>
          ))
        ) : (
          <div className="grid min-h-[120px] place-items-center rounded-lg border border-dashed border-border/50 text-sm text-ink-muted">
            <div className="text-center">
              <div className="mx-auto mb-2 flex h-10 w-10 items-center justify-center rounded-full bg-surface-elevated/40">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-ink-muted/40"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 4 6-6"/></svg>
              </div>
              <p className="text-[0.78rem]">추천 데이터가 아직 없습니다.</p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
