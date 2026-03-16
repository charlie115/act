"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { useAuth } from "../auth/AuthProvider";
import ChatMessage from "./ChatMessage";

const TYPE_FILTERS = [
  { key: "ALL", label: "전체" },
  { key: "warning", label: "경고", color: "text-amber-400" },
  { key: "info", label: "정보", color: "text-accent" },
  { key: "error", label: "에러", color: "text-red-400" },
];

export default function TelegramMessages({ visible, onNewCount }) {
  const { loggedIn, user, authorizedRequest } = useAuth();
  const containerRef = useRef(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState("ALL");

  const hasTelegram = Boolean(user?.telegram_chat_id);

  const fetchMessages = useCallback(
    async (pageNum) => {
      if (!loggedIn || !hasTelegram) {
        return;
      }

      setLoading(true);

      try {
        const payload = await authorizedRequest(
          `/api/messagecore/?page=${pageNum}`
        );
        const results = payload?.results || [];
        const reversed = [...results].reverse();

        setMessages((prev) => {
          if (pageNum === 1) {
            return reversed;
          }

          const existingIds = new Set(prev.map((m) => m.id));
          const fresh = reversed.filter((m) => !existingIds.has(m.id));

          return [...fresh, ...prev];
        });

        setHasMore(Boolean(payload?.next));
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    },
    [loggedIn, hasTelegram, authorizedRequest]
  );

  useEffect(() => {
    fetchMessages(1);

    const interval = setInterval(() => fetchMessages(1), 5000);

    return () => clearInterval(interval);
  }, [fetchMessages]);

  useEffect(() => {
    if (page > 1) {
      fetchMessages(page);
    }
  }, [page, fetchMessages]);

  const unreadCount = messages.filter((m) => !m.read).length;

  useEffect(() => {
    onNewCount?.(unreadCount);
  }, [unreadCount, onNewCount]);

  // Mark messages as read when they become visible
  useEffect(() => {
    if (!visible) {
      return;
    }

    const unreadMessages = messages.filter((m) => !m.read);

    for (const msg of unreadMessages) {
      authorizedRequest(`/api/messagecore/${msg.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ read: true }),
        headers: { "Content-Type": "application/json" },
      }).then(() => {
        setMessages((prev) =>
          prev.map((m) => (m.id === msg.id ? { ...m, read: true } : m))
        );
      }).catch(() => {});
    }
  }, [visible, messages, authorizedRequest]);

  const filtered = typeFilter === "ALL"
    ? messages
    : messages.filter((m) => m.type === typeFilter);

  if (!visible) {
    return null;
  }

  if (!loggedIn) {
    return (
      <div className="flex flex-1 items-center justify-center p-4 text-center text-xs text-ink-muted">
        로그인 후 이용 가능합니다.
      </div>
    );
  }

  if (!hasTelegram) {
    return (
      <div className="flex flex-1 items-center justify-center p-4 text-center text-xs text-ink-muted">
        텔레그램을 연결해야 메시지를 받을 수 있습니다.
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col min-h-0 overflow-hidden">
      <div className="flex items-center gap-1 border-b border-border px-2 py-1.5">
        {TYPE_FILTERS.map((filter) => (
          <button
            key={filter.key}
            className={`rounded px-2 py-0.5 text-[0.62rem] font-semibold transition-colors ${
              typeFilter === filter.key
                ? "bg-accent/20 text-accent"
                : `text-ink-muted hover:text-ink ${filter.color || ""}`
            }`}
            onClick={() => setTypeFilter(filter.key)}
            type="button"
          >
            {filter.label}
          </button>
        ))}
      </div>
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-3"
      >
        {loading && messages.length === 0 ? (
          <div className="text-center text-xs text-ink-muted py-4">로딩 중...</div>
        ) : null}
        {hasMore ? (
          <div className="text-center mb-2">
            <button
              className="text-[0.62rem] italic font-semibold text-accent hover:underline disabled:opacity-40"
              disabled={loading}
              onClick={() => setPage((p) => p + 1)}
              type="button"
            >
              더 불러오기...
            </button>
          </div>
        ) : null}
        {filtered.map((item) => (
          <ChatMessage
            key={item.id}
            datetime={item.datetime}
            id={item.id}
            isTelegram
            message={item.content}
            messageType={item.type}
            username={item.telegram_bot_username || "Bot"}
          />
        ))}
        {filtered.length === 0 && !loading ? (
          <div className="text-center text-xs text-ink-muted py-4">메시지가 없습니다.</div>
        ) : null}
      </div>
    </div>
  );
}
