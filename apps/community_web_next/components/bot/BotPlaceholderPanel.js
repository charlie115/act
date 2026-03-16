"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";

export default function BotPlaceholderPanel() {
  return (
    <div className="grid min-h-[40vh] place-items-center rounded-xl border border-border bg-surface">
      <div className="text-center space-y-2">
        <p className="text-lg font-semibold text-ink-muted">패널을 선택하세요</p>
        <p className="text-sm text-ink-muted/60">좌측 메뉴에서 원하는 기능을 선택합니다.</p>
      </div>
    </div>
  );
}
