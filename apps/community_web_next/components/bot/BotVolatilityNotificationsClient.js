"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function BotVolatilityNotificationsClient({ marketCodeCombination }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-ink">변동성 알림</h3>
      <p className="text-sm text-ink-muted py-8 text-center">알림 설정을 불러오는 중...</p>
    </div>
  );
}
