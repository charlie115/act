import { Inter } from "next/font/google";

import AppShell from "../components/AppShell";
import Providers from "../components/Providers";
import JsonLd from "../components/seo/JsonLd";
import { buildMetadata, siteConfig } from "../lib/site";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata = buildMetadata({
  title: "ArbiCrypto - 실시간 김프 차익거래 플랫폼",
});

export const viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#080c16",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <head>
        <JsonLd
          data={[
            {
              "@context": "https://schema.org",
              "@type": "WebSite",
              name: siteConfig.siteName,
              url: siteConfig.siteUrl,
              description: siteConfig.defaultDescription,
              inLanguage: "ko",
            },
            {
              "@context": "https://schema.org",
              "@type": "Organization",
              name: siteConfig.siteName,
              url: siteConfig.siteUrl,
              logo: `${siteConfig.siteUrl}/images/arbicrypto-logo.png`,
              sameAs: [siteConfig.socials.x],
            },
          ]}
        />
      </head>
      <body
        className={`${inter.variable} ${inter.className}`}
        suppressHydrationWarning
      >
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
