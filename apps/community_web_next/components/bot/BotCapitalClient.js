"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function BotCapitalClient({ marketCodeCombination }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-ink">자본 현황</h3>
      <p className="text-sm text-ink-muted py-8 text-center">자본 정보를 불러오는 중...</p>
    </div>
  );
}
