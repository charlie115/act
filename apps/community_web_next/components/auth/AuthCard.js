"use client";

export default function AuthCard({ eyebrow, title, description, children, error }) {
  return (
    <section className="auth-layout">
      <div className="auth-card">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p className="muted-copy">{description}</p>
        <div className="auth-card__body">{children}</div>
        {error ? <p className="auth-card__error">{error}</p> : null}
      </div>
    </section>
  );
}
