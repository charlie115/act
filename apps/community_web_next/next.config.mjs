const apiProxyTarget = process.env.ACW_API_PROXY_TARGET;
const backendPrefixes = [
  "auth",
  "board",
  "chat",
  "coupon",
  "exchange-status",
  "fee",
  "infocore",
  "messagecore",
  "newscore",
  "referral",
  "tradecore",
  "users",
  "wallet",
];
const publicDrfUrl = process.env.NEXT_PUBLIC_DRF_URL || process.env.NEXT_PUBLIC_SITE_URL || "";
const wsOrigin = process.env.NEXT_PUBLIC_DRF_WS_URL ||
  (publicDrfUrl ? publicDrfUrl.replace(/^http/i, "ws") : "");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  skipTrailingSlashRedirect: true,
  experimental: {
    externalDir: true,
  },
  env: {
    REACT_APP_DRF_WS_URL: wsOrigin,
    REACT_APP_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "",
    REACT_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION || "next",
  },
  async rewrites() {
    if (!apiProxyTarget) {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/:path*/`,
      },
      ...backendPrefixes.map((prefix) => ({
        source: `/${prefix}/:path*`,
        destination: `${apiProxyTarget}/${prefix}/:path*/`,
      })),
    ];
  },
};

export default nextConfig;
