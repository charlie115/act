"use client";

import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import { ChevronDown, User, Settings, LogOut } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";

export default function NextHeaderUserMenu() {
  const { user, loggedIn, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  if (!loggedIn) return null;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-ink-muted transition-colors hover:bg-surface-elevated hover:text-ink"
        type="button"
      >
        <User size={14} />
        <span className="hidden sm:inline">{user?.email?.split("@")[0]}</span>
        <ChevronDown size={12} className={`transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="absolute right-0 top-full z-50 mt-1 w-48 rounded-lg border border-border bg-surface p-1 shadow-xl">
          <Link
            href="/my-page"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 rounded-md px-3 py-2 text-sm text-ink-muted hover:bg-surface-elevated hover:text-ink"
          >
            <Settings size={14} /> 마이페이지
          </Link>
          <button
            onClick={() => { logout(); setOpen(false); }}
            className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-negative hover:bg-surface-elevated"
            type="button"
          >
            <LogOut size={14} /> 로그아웃
          </button>
        </div>
      )}
    </div>
  );
}
