"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function BotDepositClient({ marketCodeCombination }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-ink">입금 관리</h3>
      <p className="text-sm text-ink-muted py-8 text-center">입금 정보를 불러오는 중...</p>
    </div>
  );
}
