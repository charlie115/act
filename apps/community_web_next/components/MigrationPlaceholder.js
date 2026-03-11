import Link from "next/link";

export default function MigrationPlaceholder({ title, description }) {
  return (
    <section className="surface-card placeholder-card">
      <p className="eyebrow">Migration In Progress</p>
      <h1>{title}</h1>
      <p>{description}</p>
      <div className="placeholder-card__actions">
        <Link className="primary-button" href="/">
          홈으로 이동
        </Link>
        <Link className="ghost-button" href="/community-board">
          공개 페이지 보기
        </Link>
      </div>
    </section>
  );
}
