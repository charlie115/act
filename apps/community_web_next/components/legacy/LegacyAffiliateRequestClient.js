"use client";

import RequestAffiliate from "pages/RequestAffiliate";
import LegacyRouterShell from "./LegacyRouterShell";

function mapAffiliatePath(rawPath) {
  if (rawPath === "/affiliate-dashboard") {
    return "/affiliate/dashboard";
  }
  return rawPath;
}

export default function LegacyAffiliateRequestClient() {
  return (
    <div className="legacy-surface legacy-surface--affiliate">
      <LegacyRouterShell initialPath="/request-affiliate" mapPath={mapAffiliatePath}>
        <RequestAffiliate />
      </LegacyRouterShell>
    </div>
  );
}
