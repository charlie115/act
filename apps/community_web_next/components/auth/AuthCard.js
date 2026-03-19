"use client";

import Link from "next/link";

export default function AuthCard({
  eyebrow,
  title,
  description,
  children,
  error,
  highlights = [],
}) {
  return (
    <section className="grid min-h-[min(78vh,840px)] place-items-center px-4 pt-6 pb-12">
      <div className="relative w-full max-w-[480px] overflow-hidden rounded-2xl border border-border bg-background/95 shadow-2xl backdrop-blur-sm">
        {/* Decorative gradient orb */}
        <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-accent/10 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 -left-16 h-40 w-40 rounded-full bg-accent/5 blur-3xl" />

        {/* Header with logo */}
        <div className="relative border-b border-border/60 px-8 pb-6 pt-8">
          <div className="mb-5 flex items-center gap-2.5">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              alt="ArbiCrypto"
              className="h-7 w-auto"
              src="/images/logo-no-background.png"
            />
          </div>
          {eyebrow ? (
            <p className="mb-1.5 text-[0.68rem] font-bold uppercase tracking-widest text-accent">
              {eyebrow}
            </p>
          ) : null}
          <h1 className="text-xl font-bold tracking-tight text-ink">
            {title}
          </h1>
          {description ? (
            <p className="mt-1.5 text-sm leading-relaxed text-ink-muted">
              {description}
            </p>
          ) : null}
        </div>

        {/* Highlights (optional feature list) */}
        {highlights.length ? (
          <div className="grid gap-2 border-b border-border/60 px-8 py-5">
            {highlights.map((item) => (
              <div
                key={item.title}
                className="flex items-start gap-3 rounded-xl bg-surface-elevated/40 px-4 py-3"
              >
                <div className="mt-0.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-accent" />
                <div>
                  <span className="text-[0.66rem] font-bold uppercase tracking-wider text-accent/80">
                    {item.title}
                  </span>
                  <p className="mt-0.5 text-[0.82rem] leading-snug text-ink-muted">
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        ) : null}

        {/* Main content area */}
        <div className="relative px-8 pb-8 pt-6">
          <div className="grid gap-4">{children}</div>
          {error ? (
            <div className="mt-4 rounded-xl border border-warning/20 bg-warning/8 px-4 py-3">
              <p className="text-[0.82rem] font-semibold leading-relaxed text-warning">
                {error}
              </p>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
