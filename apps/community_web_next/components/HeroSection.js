import Link from "next/link";

export default function HeroSection() {
  return (
    <section className="hero">
      <div className="hero__copy">
        <p className="eyebrow">ACW Public Frontend Refresh</p>
        <h1>SEO와 초기 로딩을 먼저 살리는 Next.js 전환 베이스</h1>
        <p className="hero__description">
          기존 CRA 구조를 유지한 채 공개 페이지를 서버 렌더링으로 먼저 이동했습니다.
          뉴스, 공지, 커뮤니티 게시판은 검색 엔진과 첫 방문자에게 더 빨리 노출됩니다.
        </p>
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
        </div>
        <div className="metric-card">
          <span className="metric-card__label">SEO</span>
          <strong>Metadata API</strong>
        </div>
        <div className="metric-card">
          <span className="metric-card__label">Data Flow</span>
          <strong>DRF API / SSR fetch</strong>
        </div>
      </div>
    </section>
  );
}
