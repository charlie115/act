"use client";

import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthProvider";
import TelegramConnectButton from "../auth/TelegramConnectButton";

export default function MyPageClient() {
  const { user, authorizedRequest, loggedIn } = useAuth();
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    if (!loggedIn) return;
    authorizedRequest("/auth/user/")
      .then(setProfile)
      .catch(() => {});
  }, [loggedIn, authorizedRequest]);

  if (!profile) {
    return (
      <div className="grid min-h-[40vh] place-items-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold text-ink">마이페이지</h1>

      <div className="rounded-xl border border-border bg-surface p-6 space-y-4">
        <h2 className="text-lg font-semibold text-ink">계정 정보</h2>
        <div className="grid gap-3 text-sm">
          <div className="flex justify-between border-b border-border/50 pb-2">
            <span className="text-ink-muted">이메일</span>
            <span className="text-ink truncate min-w-0">{profile.email}</span>
          </div>
          <div className="flex justify-between border-b border-border/50 pb-2">
            <span className="text-ink-muted">텔레그램</span>
            <span className="text-ink truncate min-w-0">
              {profile.telegram_chat_id ? `연결됨 (${profile.telegram_chat_id})` : "미연결"}
            </span>
          </div>
        </div>
      </div>

      {!profile.telegram_chat_id && (
        <div className="rounded-xl border border-border bg-surface p-6 space-y-3">
          <h2 className="text-lg font-semibold text-ink">텔레그램 연결</h2>
          <p className="text-sm text-ink-muted">텔레그램을 연결하면 실시간 알림을 받을 수 있습니다.</p>
          <TelegramConnectButton botUsername={profile.socialapps?.[0]?.client_id} />
        </div>
      )}
    </div>
  );
}
