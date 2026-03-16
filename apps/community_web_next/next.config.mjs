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
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  skipTrailingSlashRedirect: true,
  env: {
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
