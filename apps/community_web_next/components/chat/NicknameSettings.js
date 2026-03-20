"use client";

import { useCallback, useRef, useState } from "react";
import { RefreshCw } from "lucide-react";

import { useAuth } from "../auth/AuthProvider";

export default function NicknameSettings({ open, onClose }) {
  const { loggedIn, user, authorizedRequest, updateUser } = useAuth();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const panelRef = useRef(null);

  const currentNickname = loggedIn
    ? user?.chat_nickname || user?.username || ""
    : (typeof window !== "undefined" && localStorage.getItem("acw-chat-nickname")) || "";

  // Logged-in: change nickname via POST
  const handleChangeNickname = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed) return;

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const data = await authorizedRequest("/chat/nickname/", {
        method: "POST",
        body: { nickname: trimmed },
      });
      if (data?.nickname) {
        updateUser({ chat_nickname: data.nickname });
        setSuccess("닉네임이 변경되었습니다");
        setInput("");
      }
    } catch (err) {
      const msg = err?.message || "닉네임 변경 실패";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [input, authorizedRequest, updateUser]);

  // Anonymous: regenerate nickname
  const handleRegenerate = useCallback(async () => {
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const res = await fetch("/api/chat/nickname/generate/");
      const data = await res.json();
      if (data?.nickname) {
        localStorage.setItem("acw-chat-nickname", data.nickname);
        setSuccess("새 닉네임이 생성되었습니다");
        // Force a page-level state update by dispatching a storage event
        window.dispatchEvent(new StorageEvent("storage", {
          key: "acw-chat-nickname",
          newValue: data.nickname,
        }));
        // Close after a short delay so user sees the success message
        setTimeout(() => onClose?.(), 800);
      }
    } catch {
      setError("닉네임 생성 실패");
    } finally {
      setLoading(false);
    }
  }, [onClose]);

  if (!open) return null;

  return (
    <div className="absolute right-0 top-full mt-1 z-50 w-64 rounded-xl border border-border/50 bg-background/98 backdrop-blur-lg shadow-xl p-3" ref={panelRef}>
      <div className="text-[0.7rem] font-semibold text-ink mb-2">닉네임 설정</div>

      <div className="text-[0.6rem] text-ink-muted/60 mb-1">현재 닉네임</div>
      <div className="text-[0.75rem] font-medium text-ink mb-3 truncate">{currentNickname || "없음"}</div>

      {loggedIn ? (
        <>
          <div className="flex gap-1.5">
            <input
              className="flex-1 rounded-lg border border-border bg-surface-elevated px-2.5 py-1.5 text-[0.75rem] text-ink placeholder:text-ink-muted/40 focus:outline-none focus:ring-1 focus:ring-accent/40"
              disabled={loading}
              maxLength={20}
              onChange={(e) => {
                setInput(e.target.value);
                setError("");
                setSuccess("");
              }}
              placeholder="새 닉네임"
              value={input}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleChangeNickname();
                }
              }}
            />
            <button
              className="rounded-lg bg-accent/20 px-2.5 py-1.5 text-[0.65rem] font-semibold text-accent hover:bg-accent/30 transition-colors disabled:opacity-40 cursor-pointer"
              disabled={loading || !input.trim()}
              onClick={handleChangeNickname}
              type="button"
            >
              변경
            </button>
          </div>
        </>
      ) : (
        <button
          className="flex items-center gap-1.5 rounded-lg bg-surface-elevated px-3 py-1.5 text-[0.65rem] font-semibold text-ink-muted hover:text-ink hover:bg-surface-elevated/70 transition-colors disabled:opacity-40 cursor-pointer"
          disabled={loading}
          onClick={handleRegenerate}
          type="button"
        >
          <RefreshCw size={12} strokeWidth={2} className={loading ? "animate-spin" : ""} />
          새 닉네임 생성
        </button>
      )}

      {error ? (
        <div className="mt-2 text-[0.6rem] text-negative">{error}</div>
      ) : null}
      {success ? (
        <div className="mt-2 text-[0.6rem] text-positive">{success}</div>
      ) : null}
    </div>
  );
}
