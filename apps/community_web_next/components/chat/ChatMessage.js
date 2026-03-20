"use client";

import { memo, useMemo } from "react";

function stringToColor(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return `hsl(${Math.abs(hash) % 360}, 55%, 60%)`;
}

function formatDatetime(datetimeStr) {
  if (!datetimeStr) return "";
  try {
    return new Date(datetimeStr).toLocaleString("ko-KR", {
      month: "numeric",
      day: "numeric",
      hour: "numeric",
      minute: "numeric",
    });
  } catch {
    return "";
  }
}

function linkifyText(text) {
  if (!text) return text;
  const urlRegex = /https?:\/\/[^\s]+/g;
  const parts = [];
  let lastIndex = 0;
  let match;
  while ((match = urlRegex.exec(text)) !== null) {
    if (match.index > lastIndex) parts.push(text.slice(lastIndex, match.index));
    parts.push(
      <a key={match.index} className="text-accent underline-offset-2 hover:underline break-all" href={match[0]} rel="noopener noreferrer" target="_blank">{match[0]}</a>
    );
    lastIndex = urlRegex.lastIndex;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts.length > 0 ? parts : text;
}

const MESSAGE_TYPE_COLORS = {
  warning: "text-warning",
  error: "text-negative",
  info: "",
};

const ChatMessage = memo(function ChatMessage({
  id, message, username, datetime, isOwnMessage, isAnon, isTelegram, messageType, onBlockUser,
}) {
  const userColor = useMemo(() => stringToColor(username || ""), [username]);
  const typeColor = isTelegram ? MESSAGE_TYPE_COLORS[messageType] || "" : "";

  return (
    <div
      id={`m-${id}`}
      className={`flex gap-2 mb-2 ${isOwnMessage ? "flex-row-reverse" : "flex-row"}`}
    >
      {/* Avatar dot */}
      {!isOwnMessage ? (
        <div className="flex-shrink-0 mt-1 relative">
          <div
            className={`h-6 w-6 rounded-full flex items-center justify-center text-[0.5rem] font-bold text-white ${isAnon ? "ring-1 ring-ink-muted/30" : ""}`}
            style={{ backgroundColor: isAnon ? "hsl(0, 0%, 45%)" : userColor }}
          >
            {(username || "?")[0].toUpperCase()}
          </div>
        </div>
      ) : null}

      <div className={`max-w-[78%] min-w-0 flex flex-col ${isOwnMessage ? "items-end" : "items-start"}`}>
        {!isOwnMessage ? (
          <div className="flex items-center gap-1.5 mb-0.5 px-1">
            <span
              className={`text-[0.65rem] font-semibold truncate max-w-[120px] ${isAnon ? "italic" : ""}`}
              style={{ color: isAnon ? "hsl(0, 0%, 55%)" : userColor }}
            >
              {username}
            </span>
            {isAnon ? (
              <span className="text-[0.5rem] font-medium px-1 py-px rounded bg-ink-muted/15 text-ink-muted/60 leading-none">
                G
              </span>
            ) : null}
            {!isTelegram && onBlockUser ? (
              <button
                className="text-[0.55rem] text-ink-muted/40 hover:text-negative transition-colors cursor-pointer"
                onClick={() => onBlockUser(username)}
                title="차단"
                type="button"
              >
                차단
              </button>
            ) : null}
          </div>
        ) : null}
        <div
          className={`relative rounded-2xl px-3 py-2 text-[0.8rem] leading-relaxed break-words whitespace-pre-wrap ${
            isOwnMessage
              ? "bg-accent/25 text-ink rounded-tl-2xl rounded-tr-2xl rounded-bl-2xl rounded-br-[4px] ring-1 ring-accent/15"
              : "bg-surface-elevated/90 text-ink rounded-tl-[4px] rounded-tr-2xl rounded-br-2xl rounded-bl-2xl"
          } ${typeColor}`}
        >
          {linkifyText(message)}
        </div>
        <span className={`mt-0.5 px-1 text-[0.55rem] text-ink-muted/40 ${isOwnMessage ? "text-right" : "text-left"}`}>
          {formatDatetime(datetime)}
        </span>
      </div>
    </div>
  );
});

export default ChatMessage;
