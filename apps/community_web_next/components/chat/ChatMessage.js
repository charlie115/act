"use client";

import { memo, useMemo } from "react";

function stringToColor(str) {
  let hash = 0;

  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }

  const hue = Math.abs(hash) % 360;

  return `hsl(${hue}, 65%, 55%)`;
}

function formatDatetime(datetimeStr) {
  if (!datetimeStr) {
    return "";
  }

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
  if (!text) {
    return text;
  }

  const urlRegex = /https?:\/\/[^\s]+/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = urlRegex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }

    parts.push(
      <a
        key={match.index}
        className="text-accent underline-offset-2 hover:underline break-all"
        href={match[0]}
        rel="noopener noreferrer"
        target="_blank"
      >
        {match[0]}
      </a>
    );
    lastIndex = urlRegex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }

  return parts.length > 0 ? parts : text;
}

const MESSAGE_TYPE_COLORS = {
  warning: "text-amber-400",
  error: "text-red-400",
  info: "",
};

const ChatMessage = memo(function ChatMessage({
  id,
  message,
  username,
  datetime,
  isOwnMessage,
  isTelegram,
  messageType,
  onBlockUser,
}) {
  const colorDot = useMemo(() => stringToColor(username || ""), [username]);
  const typeColor = isTelegram ? MESSAGE_TYPE_COLORS[messageType] || "" : "";

  return (
    <div
      id={`m-${id}`}
      className={`flex gap-2 mb-2.5 ${isOwnMessage ? "flex-row-reverse" : "flex-row"}`}
    >
      <div className={`max-w-[85%] min-w-0 ${isOwnMessage ? "items-end" : "items-start"} flex flex-col`}>
        {!isOwnMessage ? (
          <div className="flex items-center gap-1 mb-0.5">
            <span style={{ color: colorDot }} className="text-[11px] leading-none">
              &#9679;
            </span>
            <span className="text-[0.68rem] text-ink-muted font-medium">
              @{username}
            </span>
            {!isTelegram && onBlockUser ? (
              <button
                className="text-[0.6rem] text-ink-muted/60 hover:text-red-400 transition-colors"
                onClick={() => onBlockUser(username)}
                title="차단"
                type="button"
              >
                &#x26D4;
              </button>
            ) : null}
          </div>
        ) : null}
        <div
          className={`relative rounded-lg px-3 py-2 text-[0.78rem] leading-snug break-words whitespace-pre-wrap ${
            isOwnMessage
              ? "bg-accent/20 text-ink rounded-br-sm"
              : "bg-surface-elevated text-ink rounded-bl-sm"
          } ${typeColor}`}
        >
          {linkifyText(message)}
          <span className="block mt-1 text-[0.6rem] text-ink-muted/60 text-right">
            {formatDatetime(datetime)}
          </span>
        </div>
      </div>
    </div>
  );
});

export default ChatMessage;
