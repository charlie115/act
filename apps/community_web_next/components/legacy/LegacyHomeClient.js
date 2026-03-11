"use client";

import Box from "@mui/material/Box";

import Home from "../../../community_web/src/pages/Home";
import TVTickerWidget from "../../../community_web/src/components/trading_view/TVTickerWidget";

export default function LegacyHomeClient() {
  return (
    <Box sx={{ width: "100%" }}>
      <TVTickerWidget isVisible />
      <Home />
    </Box>
  );
}
