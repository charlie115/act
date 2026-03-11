import Link from "next/link";

export default function ArbitrageLayout({ currentTab, children }) {
  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Arbitrage</p>
            <h1>Funding Rate Explorer</h1>
          </div>
          <div className="tab-strip">
            <Link
              className={`tab-pill${currentTab === "diff" ? " tab-pill--active" : ""}`}
              href="/arbitrage/funding-rate/diff"
            >
              Funding Rate Diff
            </Link>
            <Link
              className={`tab-pill${currentTab === "avg" ? " tab-pill--active" : ""}`}
              href="/arbitrage/funding-rate/avg"
            >
              Average Funding Rate
            </Link>
          </div>
        </div>
      </section>
      {children}
    </div>
  );
}
