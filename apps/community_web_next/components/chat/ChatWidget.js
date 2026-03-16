"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { MessageCircle, X } from "lucide-react";

import TelegramMessages from "./TelegramMessages";
import CommunityMessages from "./CommunityMessages";

const CHANNELS = [
  { key: "community", label: "커뮤니티" },
  { key: "telegram", label: "텔레그램" },
];

function ChannelTabs({ channel, onChangeChannel, communityBadge, telegramBadge }) {
  return (
    <div className="flex border-b border-border">
      {CHANNELS.map((ch) => {
        const badge = ch.key === "community" ? communityBadge : telegramBadge;

        return (
          <button
            key={ch.key}
            className={`flex-1 py-2 text-center text-[0.72rem] font-semibold transition-colors ${
              channel === ch.key
                ? "border-b-2 border-accent text-accent"
                : "text-ink-muted hover:text-ink"
            }`}
            onClick={() => onChangeChannel(ch.key)}
            type="button"
          >
            {ch.label}
            {badge > 0 ? (
              <span className="ml-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500/90 px-1 text-[0.52rem] font-bold text-white">
                {badge}
              </span>
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
  const panelRef = useRef(null);

  const totalBadge = communityBadge + telegramBadge;

  // Close mobile popup on outside click
  useEffect(() => {
    if (!open) {
      return;
    }

    function handlePointerDown(event) {
      if (panelRef.current && !panelRef.current.contains(event.target)) {
        setOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    window.addEventListener("pointerdown", handlePointerDown);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("pointerdown", handlePointerDown);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const handleCommunityCount = useCallback((count) => setCommunityBadge(count), []);
  const handleTelegramCount = useCallback((count) => setTelegramBadge(count), []);

  return (
    <>
      {/* ── Desktop: docked sidebar on the right ── */}
      <aside className="hidden min-[1600px]:flex fixed right-0 top-0 bottom-0 z-30 w-[320px] flex-col border-l border-border bg-background/98 backdrop-blur-sm">
        {/* Header */}
        <div className="flex items-center gap-2 border-b border-border px-3 py-2.5" style={{ minHeight: 56 }}>
          <MessageCircle size={16} strokeWidth={2} className="text-accent" />
          <span className="text-sm font-bold text-ink">Chat</span>
        </div>

        {/* Channel tabs */}
        <ChannelTabs
          channel={channel}
          communityBadge={communityBadge}
          onChangeChannel={setChannel}
          telegramBadge={telegramBadge}
        />

        {/* Messages */}
        <MessagesArea
          channel={channel}
          onCommunityCount={handleCommunityCount}
          onTelegramCount={handleTelegramCount}
        />
      </aside>

      {/* ── Mobile/Tablet: FAB + popup ── */}
      <div className="min-[1600px]:hidden">
        {/* FAB button */}
        <div className="fixed bottom-4 right-4 z-50">
          <button
            className="relative inline-flex items-center gap-1.5 rounded-full bg-accent px-3 py-3 text-white shadow-lg transition-all hover:shadow-xl hover:bg-accent/90 active:scale-95"
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            onClick={(event) => {
              event.stopPropagation();
              setOpen((prev) => !prev);
            }}
            type="button"
          >
            {open ? <X size={20} strokeWidth={2} /> : <MessageCircle size={20} strokeWidth={2} />}
            {(hovered || open) ? (
              <span className="text-[0.78rem] font-bold">Chat</span>
            ) : null}
            {!open && totalBadge > 0 ? (
              <span className="absolute -top-1 -left-1 inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[0.6rem] font-bold text-white">
                {totalBadge > 99 ? "99+" : totalBadge}
              </span>
            ) : null}
          </button>
        </div>

        {/* Popup panel */}
        {open ? (
          <div
            ref={panelRef}
            className="fixed bottom-20 right-4 z-50 flex flex-col overflow-hidden rounded-xl border border-border bg-background shadow-2xl"
            style={{ width: "min(350px, calc(100vw - 32px))", height: "min(500px, calc(100vh - 120px))" }}
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border bg-accent px-3 py-2">
              <div className="flex items-center gap-2">
                <MessageCircle size={16} strokeWidth={2} className="text-white" />
                <span className="text-sm font-bold text-white">Chat</span>
              </div>
              <button
                className="inline-flex h-7 w-7 items-center justify-center rounded-lg text-white/70 transition-colors hover:bg-white/10 hover:text-white"
                onClick={() => setOpen(false)}
                type="button"
              >
                <X size={16} strokeWidth={2} />
              </button>
            </div>

            {/* Channel tabs */}
            <ChannelTabs
              channel={channel}
              communityBadge={communityBadge}
              onChangeChannel={setChannel}
              telegramBadge={telegramBadge}
            />

            {/* Messages */}
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
