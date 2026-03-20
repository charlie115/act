"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAuth } from "../auth/AuthProvider";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

function msgKey(m) {
  return `${m.username}-${m.datetime}-${(m.message || "").slice(0, 20)}`;
}

export default function CommunityMessages({ visible, onNewCount }) {
  const { user, loggedIn } = useAuth();
  const containerRef = useRef(null);
  const wsRef = useRef(null);
  const shouldScrollRef = useRef(true);
  const [messages, setMessages] = useState([]);
  const [newMessageIds, setNewMessageIds] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [page, setPage] = useState(1);
  const [blocklist, setBlocklist] = useState(() => {
    if (typeof window === "undefined") {
      return [];
    }

    try {
      return JSON.parse(localStorage.getItem("acw-chat-blocklist") || "[]");
    } catch {
      return [];
    }
  });

  const username = user?.username || "";

  // Persist blocklist
  useEffect(() => {
    try {
      localStorage.setItem("acw-chat-blocklist", JSON.stringify(blocklist));
    } catch {
      // ignore
    }
  }, [blocklist]);

  // Scroll to bottom helper
  const scrollToBottom = useCallback(() => {
    const container = containerRef.current;
    if (container) {
      requestAnimationFrame(() => {
        container.scrollTop = container.scrollHeight;
      });
    }
  }, []);

  // Fetch past messages via REST
  const fetchPastMessages = useCallback(
    async (pageNum) => {
      setLoading(true);

      try {
        const response = await fetch(`/api/chat/past/?page=${pageNum}`);
        const payload = await response.json();
        const results = payload?.results || payload || [];
        const reversed = [...results].reverse();

        setMessages((prev) => {
          if (pageNum === 1) {
            return reversed;
          }

          const existingIds = new Set(prev.map(msgKey));
          const fresh = reversed.filter((m) => !existingIds.has(msgKey(m)));

          return [...fresh, ...prev];
        });

        setHasMore(Boolean(payload?.next));

        if (pageNum === 1) {
          shouldScrollRef.current = true;
        }
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchPastMessages(1);
  }, [fetchPastMessages]);

  useEffect(() => {
    if (page > 1) {
      fetchPastMessages(page);
    }
  }, [page, fetchPastMessages]);

  // WebSocket connection for real-time messages
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_DRF_WS_URL || process.env.REACT_APP_DRF_WS_URL;

    if (!wsUrl || !loggedIn) {
      return;
    }

    const wsEndpoint = `${wsUrl}/chat/`;
    let ws;
    let reconnectTimeout;

    function connect() {
      ws = new WebSocket(wsEndpoint);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("[Chat] WebSocket connected");
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const msg = data?.message || data;

          if (msg && msg.username && msg.datetime) {
            setMessages((prev) => {
              const key = msgKey(msg);
              // If exact key exists, skip
              if (prev.some((m) => msgKey(m) === key && !m._optimistic)) {
                return prev;
              }
              // Replace optimistic message from same user with server version
              const optimisticIdx = prev.findIndex(
                (m) => m._optimistic && m.username === msg.username && m.message === msg.message
              );
              if (optimisticIdx !== -1) {
                const next = [...prev];
                next[optimisticIdx] = msg;
                return next;
              }
              return [...prev, msg];
            });

            if (msg.username !== username) {
              const key = msgKey(msg);
              setNewMessageIds((prev) => new Set(prev).add(key));
            }

            // Only auto-scroll if user is near the bottom
            const el = containerRef.current;
            if (el) {
              const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
              if (nearBottom || msg.username === username) {
                shouldScrollRef.current = true;
              }
            }
          }
        } catch {
          // ignore malformed
        }
      };

      ws.onerror = (err) => {
        console.warn("[Chat] WebSocket error", err);
      };

      ws.onclose = () => {
        wsRef.current = null;
        if (!destroyed) {
          reconnectTimeout = setTimeout(connect, 2000);
        }
      };
    }

    let destroyed = false;
    connect();

    return () => {
      destroyed = true;
      clearTimeout(reconnectTimeout);
      if (ws) {
        ws.onclose = null;
        ws.close();
      }
    };
  }, [username, loggedIn]);

  // Report badge count
  useEffect(() => {
    onNewCount?.(newMessageIds.size);
  }, [newMessageIds.size, onNewCount]);

  // Clear new message badges when tab becomes visible
  useEffect(() => {
    if (visible) {
      setNewMessageIds(new Set());
    }
  }, [visible]);

  // Scroll to bottom when visible or new messages
  useEffect(() => {
    if (visible && shouldScrollRef.current) {
      scrollToBottom();
      shouldScrollRef.current = false;
    }
  }, [visible, messages, scrollToBottom]);

  function handleSend(text) {
    // Optimistic local add
    const now = new Date().toISOString();
    const localMsg = {
      username,
      email: user?.email || "",
      message: text,
      datetime: now,
      _optimistic: true,
    };

    setMessages((prev) => [...prev, localMsg]);
    shouldScrollRef.current = true;

    // Send via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN && username) {
      wsRef.current.send(
        JSON.stringify({
          username,
          email: user?.email || "",
          message: text,
        })
      );
    }
  }

  const handleBlock = useCallback((blockedUsername) => {
    setBlocklist((prev) =>
      prev.includes(blockedUsername) ? prev : [...prev, blockedUsername]
    );
  }, []);

  const filtered = useMemo(() =>
    messages.filter(
      (m) => !blocklist.includes(m.username) && !(m.username !== username && m.status === "BLOCKED")
    ),
    [messages, blocklist, username]
  );

  return (
    <div className={`flex flex-1 flex-col min-h-0 overflow-hidden ${visible ? "" : "hidden"}`}>
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
        {filtered.map((item, idx) => (
          <ChatMessage
            key={msgKey(item)}
            datetime={item.datetime}
            id={item.id}
            isOwnMessage={item.username === username}
            message={item.message}
            username={item.username}
            onBlockUser={handleBlock}
          />
        ))}
        {filtered.length === 0 && !loading ? (
          <div className="text-center text-xs text-ink-muted py-4">메시지가 없습니다.</div>
        ) : null}
      </div>
      <ChatInput disabled={!loggedIn || !username} onSend={handleSend} />
    </div>
  );
}
