import path from "path";

const apiProxyTarget = process.env.ACW_API_PROXY_TARGET;
const legacySrc = path.resolve("../community_web/src");
const legacyNextCompat = path.resolve("./legacy");
const publicDrfUrl = process.env.NEXT_PUBLIC_DRF_URL || process.env.NEXT_PUBLIC_SITE_URL || "";
const wsOrigin = process.env.NEXT_PUBLIC_DRF_WS_URL ||
  (publicDrfUrl ? publicDrfUrl.replace(/^http/i, "ws") : "");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  experimental: {
    externalDir: true,
  },
  env: {
    REACT_APP_DRF_WS_URL: wsOrigin,
    REACT_APP_GOOGLE_CLIENT_ID: process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "",
    REACT_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION || "next",
  },
  webpack(config) {
    config.resolve.modules = [
      path.resolve("./node_modules"),
      ...(config.resolve.modules || []),
    ];

    config.resolve.alias = {
      ...(config.resolve.alias || {}),
      assets: path.join(legacySrc, "assets"),
      "@emotion/react": path.resolve("./node_modules/@emotion/react"),
      "@emotion/styled": path.resolve("./node_modules/@emotion/styled"),
      "@mui/icons-material": path.resolve("./node_modules/@mui/icons-material"),
      "@mui/lab": path.resolve("./node_modules/@mui/lab"),
      "@mui/material": path.resolve("./node_modules/@mui/material"),
      "@mui/x-date-pickers": path.resolve("./node_modules/@mui/x-date-pickers"),
      "@reduxjs/toolkit": path.resolve("./node_modules/@reduxjs/toolkit"),
      "@uidotdev/usehooks": path.resolve("./node_modules/@uidotdev/usehooks"),
      components: path.join(legacySrc, "components"),
      configs: path.join(legacySrc, "configs"),
      constants: path.join(legacySrc, "constants"),
      contexts: path.join(legacySrc, "contexts"),
      hooks: path.join(legacySrc, "hooks"),
      i18next: path.resolve("./node_modules/i18next"),
      "lightweight-charts": path.resolve("./node_modules/lightweight-charts"),
      lodash: path.resolve("./node_modules/lodash"),
      luxon: path.resolve("./node_modules/luxon"),
      "react-hook-form": path.resolve("./node_modules/react-hook-form"),
      "react-i18next": path.resolve("./node_modules/react-i18next"),
      "react-redux": path.resolve("./node_modules/react-redux"),
      "react-router-dom": path.resolve("./node_modules/react-router-dom"),
      "redux$": path.resolve("./node_modules/redux"),
      "redux-persist": path.resolve("./node_modules/redux-persist"),
      redux: path.join(legacySrc, "redux"),
      utils: path.join(legacySrc, "utils"),
      "configs/theme$": path.join(legacyNextCompat, "configs/theme/index.js"),
    };

    config.module.rules.push({
      test: /\.(png|jpe?g|gif|svg)$/i,
      type: "asset/resource",
    });

    return config;
  },
  async rewrites() {
    if (!apiProxyTarget) {
      return [];
    }

    return [
      {
        source: "/api/:path*",
        destination: `${apiProxyTarget}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
