"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function BotScannerClient({ marketCodeCombination }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-ink">마켓 스캐너</h3>
      <p className="text-sm text-ink-muted py-8 text-center">스캐너 데이터를 불러오는 중...</p>
    </div>
  );
}
