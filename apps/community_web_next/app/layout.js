import { Inter } from "next/font/google";

import AppShell from "../components/AppShell";
import Providers from "../components/Providers";
import { buildMetadata } from "../lib/site";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const metadata = buildMetadata({
  title: "ACW Next",
});

export const viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#080c16",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
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
