import Link from "next/link";

import AuthActions from "./auth/AuthActions";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/news", label: "News" },
  { href: "/community-board", label: "Board" },
  { href: "/arbitrage", label: "Arbitrage" },
  { href: "/bot", label: "Bot" },
];

export default function AppShell({ children }) {
  return (
    <div className="site-shell">
      <header className="site-header">
        <div className="site-header__inner">
          <Link className="site-brand" href="/">
            <span className="site-brand__mark">ACW</span>
            <span className="site-brand__text">ArbiCrypto Next</span>
          </Link>
          <nav className="site-nav" aria-label="Main navigation">
            {navItems.map((item) => (
              <Link key={item.href} className="site-nav__link" href={item.href}>
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="site-header__actions">
            <AuthActions />
          </div>
        </div>
      </header>
      <main className="page-frame">{children}</main>
      <footer className="site-footer">
        <div>
          <strong>ACW Next</strong>
          <p>SSR-first public frontend for SEO, speed, and cleaner routing.</p>
        </div>
        <div className="site-footer__meta">
          <span>Powered by Next.js</span>
          <span>Backed by community_drf</span>
        </div>
      </footer>
    </div>
  );
}
