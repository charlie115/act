import Link from "next/link";

export default function NotFound() {
  return (
    <section className="surface-card placeholder-card">
      <p className="eyebrow">404</p>
      <h1>페이지를 찾을 수 없습니다.</h1>
      <p>요청한 경로가 아직 마이그레이션되지 않았거나 존재하지 않습니다.</p>
      <div className="placeholder-card__actions">
        <Link className="primary-button" href="/">
          홈으로 이동
        </Link>
      </div>
    </section>
  );
}
