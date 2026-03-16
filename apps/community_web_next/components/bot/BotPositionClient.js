"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function BotPositionClient({ marketCodeCombination }) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-ink">포지션 현황</h3>
      <p className="text-sm text-ink-muted py-8 text-center">활성 포지션이 없습니다.</p>
    </div>
  );
}
