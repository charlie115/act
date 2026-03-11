import { Inter, JetBrains_Mono } from "next/font/google";

import AppShell from "../components/AppShell";
import Providers from "../components/Providers";
import { buildMetadata } from "../lib/site";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

const jetBrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata = buildMetadata({
  title: "ACW Next",
});

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body className={`${inter.variable} ${jetBrainsMono.variable}`}>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
