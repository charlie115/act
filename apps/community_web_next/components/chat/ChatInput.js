"use client";

import { useRef, useState } from "react";
import { Send } from "lucide-react";

export default function ChatInput({ onSend, disabled }) {
  const inputRef = useRef(null);
  const composingRef = useRef(false);
  const justSentRef = useRef(false);
  const [message, setMessage] = useState("");

  function handleSubmit() {
    if (justSentRef.current) return;
    const text = message.trim();
    if (!text || !onSend) return;

    justSentRef.current = true;
    onSend(text);
    setMessage("");

    // Force-clear the DOM value to prevent IME residual characters
    if (inputRef.current) {
      inputRef.current.value = "";
    }

    // Ignore onChange for a short window after submit
    requestAnimationFrame(() => {
      setTimeout(() => {
        justSentRef.current = false;
      }, 100);
    });

    inputRef.current?.focus();
  }

  return (
    <div className={`flex items-end gap-1.5 border-t border-border p-2 ${disabled ? "opacity-40 pointer-events-none" : ""}`}>
      <textarea
        ref={inputRef}
        className="flex-1 resize-none rounded-lg border border-border bg-surface-elevated px-3 py-2 text-base text-ink placeholder:text-ink-muted/50 focus:outline-none focus:ring-1 focus:ring-accent/40"
        disabled={disabled}
        maxLength={500}
        onChange={(event) => {
          if (justSentRef.current) return;
          const val = event.target.value;
          if (val !== "\n") {
            setMessage(val);
          }
        }}
        onCompositionStart={() => { composingRef.current = true; }}
        onCompositionEnd={() => { composingRef.current = false; }}
        onKeyDown={(event) => {
          if (event.key === "Enter" && !event.shiftKey && !composingRef.current && event.keyCode !== 229) {
            event.preventDefault();
            handleSubmit();
          }
        }}
        placeholder="메시지 입력..."
        rows={2}
        value={message}
      />
      <button
        className="inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg text-accent transition-colors hover:bg-accent/10 disabled:text-ink-muted/40"
        disabled={!/\S/.test(message)}
        onClick={handleSubmit}
        title="전송"
        type="button"
      >
        <Send size={16} strokeWidth={2} />
      </button>
    </div>
  );
}
