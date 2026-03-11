import Link from "next/link";

export default function HeroSection() {
  return (
    <section className="hero">
      <div className="hero__copy">
        <p className="eyebrow">ACW Intelligence Layer</p>
        <h1>시장 감시, 커뮤니티, 실행 흐름을 한 화면 안에서 더 선명하게.</h1>
        <p className="hero__description">
          Next 기반 새 프론트는 공개 정보 탐색 속도를 끌어올리고, 인증 이후 제어 화면까지
          하나의 일관된 작업 공간으로 묶습니다. 데이터는 빠르게, 인터페이스는 더 또렷하게 보여줍니다.
        </p>
        <div className="hero__ticker">
          <span>Funding Explorer</span>
          <span>Bot Controls</span>
          <span>Community Signals</span>
          <span>Affiliate Ops</span>
        </div>
        <div className="hero__actions">
          <Link className="primary-button" href="/news">
            최신 뉴스 보기
          </Link>
          <Link className="ghost-button" href="/community-board">
            커뮤니티 보드 보기
          </Link>
        </div>
      </div>
      <div className="hero__panel">
        <div className="metric-card">
          <span className="metric-card__label">Rendering</span>
          <strong>Server-first</strong>
          <p>Public routes are tuned for fast first paint and stable navigation.</p>
        </div>
        <div className="metric-card">
          <span className="metric-card__label">SEO</span>
          <strong>Metadata API</strong>
          <p>Canonical metadata and crawlable public information are emitted at render time.</p>
        </div>
        <div className="metric-card">
          <span className="metric-card__label">Workflow</span>
          <strong>Trading + Community</strong>
          <p>Market discovery, posting, affiliate tools, and bot operations sit on one visual system.</p>
        </div>
      </div>
    </section>
  );
}
