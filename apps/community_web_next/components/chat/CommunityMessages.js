"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { useAuth } from "../auth/AuthProvider";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";

function msgKey(m) {
  return `${m.nickname || m.username}-${m.datetime}-${(m.message || "").slice(0, 20)}`;
}

export default function CommunityMessages({ visible, onNewCount }) {
  const { user, token, loggedIn } = useAuth();
  const containerRef = useRef(null);
  const wsRef = useRef(null);
  const shouldScrollRef = useRef(true);
  const [messages, setMessages] = useState([]);
  const [newMessageIds, setNewMessageIds] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [hasMore, setHasMore] = useState(false);
  const [page, setPage] = useState(1);
  const [nickname, setNickname] = useState("");
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

  // Resolve nickname: logged-in users use user.chat_nickname, anon users use localStorage or fetch one
  useEffect(() => {
    if (loggedIn && user?.chat_nickname) {
      setNickname(user.chat_nickname);
      return;
    }

    if (loggedIn) {
      // Logged in but no chat_nickname yet — use username as fallback
      setNickname(user?.username || "");
      return;
    }

    // Anonymous: check localStorage first
    const stored = localStorage.getItem("acw-chat-nickname");
    if (stored) {
      setNickname(stored);
      return;
    }

    // Fetch a generated nickname
    let cancelled = false;
    fetch("/api/chat/nickname/generate/")
      .then((res) => res.json())
      .then((data) => {
        if (!cancelled && data?.nickname) {
          localStorage.setItem("acw-chat-nickname", data.nickname);
          setNickname(data.nickname);
        }
      })
      .catch(() => {
        // ignore
      });

    return () => { cancelled = true; };
  }, [loggedIn, user?.chat_nickname, user?.username]);

  // Listen for anonymous nickname changes from NicknameSettings
  useEffect(() => {
    if (loggedIn) return;

    function handleStorage(e) {
      if (e.key === "acw-chat-nickname" && e.newValue) {
        setNickname(e.newValue);
      }
    }

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [loggedIn]);

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

  // WebSocket connection for real-time messages (connects regardless of login status)
  useEffect(() => {
    const wsUrl = process.env.NEXT_PUBLIC_DRF_WS_URL || process.env.REACT_APP_DRF_WS_URL;

    if (!wsUrl) {
      return;
    }

    const wsEndpoint = token
      ? `${wsUrl}/chat/?token=${encodeURIComponent(token)}`
      : `${wsUrl}/chat/`;
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
          const displayName = msg.nickname || msg.username;

          if (msg && displayName && msg.datetime) {
            setMessages((prev) => {
              const key = msgKey(msg);
              // If exact key exists, skip
              if (prev.some((m) => msgKey(m) === key && !m._optimistic)) {
                return prev;
              }
              // Replace optimistic message from same user with server version
              const optimisticIdx = prev.findIndex(
                (m) => m._optimistic && (m.nickname || m.username) === displayName && m.message === msg.message
              );
              if (optimisticIdx !== -1) {
                const next = [...prev];
                next[optimisticIdx] = msg;
                return next;
              }
              return [...prev, msg];
            });

            if (displayName !== nickname) {
              const key = msgKey(msg);
              setNewMessageIds((prev) => new Set(prev).add(key));
            }

            // Only auto-scroll if user is near the bottom
            const el = containerRef.current;
            if (el) {
              const nearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 100;
              if (nearBottom || displayName === nickname) {
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
  }, [nickname, token]);

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
    if (!nickname) return;

    const isAnon = !loggedIn;

    // Optimistic local add
    const now = new Date().toISOString();
    const localMsg = {
      nickname,
      username: nickname,
      email: user?.email || "",
      message: text,
      datetime: now,
      is_anon: isAnon,
      _optimistic: true,
    };

    setMessages((prev) => [...prev, localMsg]);
    shouldScrollRef.current = true;

    // Send via WebSocket
    if (wsRef.current?.readyState === WebSocket.OPEN && nickname) {
      wsRef.current.send(
        JSON.stringify({
          nickname,
          username: nickname,
          email: user?.email || "",
          message: text,
          is_anon: isAnon,
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
      (m) => {
        const name = m.nickname || m.username;
        return !blocklist.includes(name) && !(name !== nickname && m.status === "BLOCKED");
      }
    ),
    [messages, blocklist, nickname]
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
        {filtered.map((item) => (
          <ChatMessage
            key={msgKey(item)}
            datetime={item.datetime}
            id={item.id}
            isAnon={Boolean(item.is_anon)}
            isOwnMessage={(item.nickname || item.username) === nickname}
            message={item.message}
            username={item.nickname || item.username}
            onBlockUser={handleBlock}
          />
        ))}
        {filtered.length === 0 && !loading ? (
          <div className="text-center text-xs text-ink-muted py-4">메시지가 없습니다.</div>
        ) : null}
      </div>
      <ChatInput disabled={!nickname} nickname={nickname} onSend={handleSend} />
    </div>
  );
}
