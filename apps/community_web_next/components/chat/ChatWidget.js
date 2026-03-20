"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { MessageCircle, X, Settings } from "lucide-react";

import TelegramMessages from "./TelegramMessages";
import CommunityMessages from "./CommunityMessages";
import NicknameSettings from "./NicknameSettings";

const CHANNELS = [
  { key: "community", label: "커뮤니티" },
  { key: "telegram", label: "텔레그램" },
];

function ChannelTabs({ channel, onChangeChannel, communityBadge, telegramBadge }) {
  return (
    <div className="flex bg-surface-elevated/30">
      {CHANNELS.map((ch) => {
        const badge = ch.key === "community" ? communityBadge : telegramBadge;
        const active = channel === ch.key;

        return (
          <button
            key={ch.key}
            className={`relative flex-1 py-2.5 text-center text-[0.72rem] font-semibold transition-all duration-200 cursor-pointer ${
              active
                ? "text-accent"
                : "text-ink-muted/60 hover:text-ink-muted"
            }`}
            onClick={() => onChangeChannel(ch.key)}
            type="button"
          >
            {ch.label}
            {badge > 0 ? (
              <span className="ml-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-negative px-1 text-[0.5rem] font-bold text-white">
                {badge > 99 ? "99+" : badge}
              </span>
            ) : null}
            {active ? (
              <span className="absolute bottom-0 left-1/4 right-1/4 h-[2px] rounded-full bg-accent" />
            ) : null}
          </button>
        );
      })}
    </div>
  );
}

function MessagesArea({ channel, onCommunityCount, onTelegramCount }) {
  return (
    <>
      <CommunityMessages
        visible={channel === "community"}
        onNewCount={onCommunityCount}
      />
      <TelegramMessages
        visible={channel === "telegram"}
        onNewCount={onTelegramCount}
      />
    </>
  );
}

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [channel, setChannel] = useState("community");
  const [communityBadge, setCommunityBadge] = useState(0);
  const [telegramBadge, setTelegramBadge] = useState(0);
  const [nicknameOpen, setNicknameOpen] = useState(false);
  const panelRef = useRef(null);

  const totalBadge = communityBadge + telegramBadge;

  useEffect(() => {
    if (!open) return;

    function handlePointerDown(event) {
      if (panelRef.current && !panelRef.current.contains(event.target)) {
        setOpen(false);
        setNicknameOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        if (nicknameOpen) {
          setNicknameOpen(false);
        } else {
          setOpen(false);
        }
      }
    }

    window.addEventListener("pointerdown", handlePointerDown);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("pointerdown", handlePointerDown);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open, nicknameOpen]);

  const handleCommunityCount = useCallback((count) => setCommunityBadge(count), []);
  const handleTelegramCount = useCallback((count) => setTelegramBadge(count), []);

  return (
    <>
      {/* ── Desktop: docked sidebar ── */}
      <aside className="hidden min-[1440px]:flex fixed right-0 top-0 bottom-0 z-30 w-[320px] flex-col border-l border-border/40 bg-background/95 backdrop-blur-lg">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/30 bg-gradient-to-r from-accent/10 to-transparent">
          <div className="flex items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/15">
              <MessageCircle size={14} strokeWidth={2} className="text-accent" />
            </div>
            <span className="text-sm font-bold text-ink tracking-tight">채팅</span>
          </div>
          <div className="relative">
            <button
              className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-ink-muted/50 transition-colors hover:bg-surface-elevated hover:text-ink cursor-pointer"
              onClick={() => setNicknameOpen((prev) => !prev)}
              title="닉네임 설정"
              type="button"
            >
              <Settings size={14} strokeWidth={2} />
            </button>
            <NicknameSettings open={nicknameOpen} onClose={() => setNicknameOpen(false)} />
          </div>
        </div>
        <ChannelTabs
          channel={channel}
          communityBadge={communityBadge}
          onChangeChannel={setChannel}
          telegramBadge={telegramBadge}
        />
        <MessagesArea
          channel={channel}
          onCommunityCount={handleCommunityCount}
          onTelegramCount={handleTelegramCount}
        />
      </aside>

      {/* ── Mobile/Tablet: FAB + popup ── */}
      <div className="min-[1440px]:hidden">
        {/* FAB */}
        <div className="fixed bottom-4 right-4 z-50">
          <button
            className={`group relative inline-flex items-center gap-1.5 rounded-full px-3.5 py-3.5 text-white shadow-lg transition-all duration-200 cursor-pointer ${
              open
                ? "bg-ink-muted/80 hover:bg-ink-muted/70 shadow-md"
                : "bg-accent shadow-[0_8px_24px_-4px_rgba(43,115,255,0.5)] hover:shadow-[0_12px_32px_-4px_rgba(43,115,255,0.65)] hover:scale-105 active:scale-95"
            }`}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            onClick={(event) => {
              event.stopPropagation();
              setOpen((prev) => {
                if (prev) setNicknameOpen(false);
                return !prev;
              });
            }}
            type="button"
          >
            {open ? <X size={20} strokeWidth={2} /> : <MessageCircle size={20} strokeWidth={2} />}
            {!open && totalBadge > 0 ? (
              <span className="absolute -top-1.5 -right-1.5 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-negative px-1 text-[0.58rem] font-bold text-white shadow-sm animate-pulse">
                {totalBadge > 99 ? "99+" : totalBadge}
              </span>
            ) : null}
          </button>
        </div>

        {/* Popup */}
        {open ? (
          <div
            ref={panelRef}
            className="fixed bottom-[72px] right-3 sm:right-4 z-50 flex flex-col overflow-hidden rounded-2xl border border-border/40 bg-background/95 backdrop-blur-lg shadow-[0_16px_48px_-8px_rgba(0,0,0,0.4)]"
            style={{ width: "min(360px, calc(100vw - 24px))", height: "min(520px, calc(100vh - 100px))", animation: "fadeSlideUp 0.25s cubic-bezier(0.16, 1, 0.3, 1)" }}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-accent/15 to-transparent border-b border-border/30">
              <div className="flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent/20">
                  <MessageCircle size={14} strokeWidth={2} className="text-accent" />
                </div>
                <span className="text-sm font-bold text-ink tracking-tight">채팅</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="relative">
                  <button
                    className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-ink-muted/50 transition-colors hover:bg-surface-elevated hover:text-ink cursor-pointer"
                    onClick={() => setNicknameOpen((prev) => !prev)}
                    title="닉네임 설정"
                    type="button"
                  >
                    <Settings size={14} strokeWidth={2} />
                  </button>
                  <NicknameSettings open={nicknameOpen} onClose={() => setNicknameOpen(false)} />
                </div>
                <button
                  className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-ink-muted/60 transition-colors hover:bg-surface-elevated hover:text-ink cursor-pointer"
                  onClick={() => { setOpen(false); setNicknameOpen(false); }}
                  type="button"
                >
                  <X size={15} strokeWidth={2} />
                </button>
              </div>
            </div>

            <ChannelTabs
              channel={channel}
              communityBadge={communityBadge}
              onChangeChannel={setChannel}
              telegramBadge={telegramBadge}
            />

            <MessagesArea
              channel={channel}
              onCommunityCount={handleCommunityCount}
              onTelegramCount={handleTelegramCount}
            />
          </div>
        ) : null}
      </div>
    </>
  );
}
