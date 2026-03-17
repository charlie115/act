"use client";

import { useEffect, useState } from "react";
import { ArrowUp } from "lucide-react";

export default function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    function handleScroll() {
      setVisible(window.scrollY > 400);
    }

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  if (!visible) {
    return null;
  }

  return (
    <button
      aria-label="맨 위로"
      className="fixed bottom-20 right-6 z-30 flex h-10 w-10 items-center justify-center rounded-full border border-border bg-surface-elevated/90 text-ink-muted shadow-lg backdrop-blur transition-all hover:border-accent/30 hover:text-accent hover:shadow-accent/10"
      onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
      type="button"
    >
      <ArrowUp size={18} strokeWidth={2} />
    </button>
  );
}
