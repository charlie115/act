"use client";

import Box from "@mui/material/Box";

import Home from "pages/Home";
import TVTickerWidget from "components/trading_view/TVTickerWidget";
import LegacyRouterShell from "./LegacyRouterShell";

export default function LegacyHomeClient() {
  return (
    <Box className="legacy-surface legacy-surface--home" sx={{ width: "100%" }}>
      <TVTickerWidget isVisible />
      <LegacyRouterShell initialPath="/">
        <Home />
      </LegacyRouterShell>
    </Box>
  );
}
