"use client";

import { AlertTriangle } from "lucide-react";

export default function GlobalError({ error, reset }) {
  return (
    <div className="mx-auto grid min-h-[60vh] w-[min(600px,90vw)] place-items-center">
      <div className="grid gap-4 text-center">
        <AlertTriangle size={48} className="mx-auto text-negative/70" strokeWidth={1.5} />
        <div>
          <h2 className="mb-1 text-lg font-bold text-ink">오류가 발생했습니다</h2>
          <p className="text-sm text-ink-muted">
            {error?.message || "알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}
          </p>
        </div>
        <button
          className="mx-auto inline-flex items-center gap-2 rounded-lg border border-accent/30 bg-accent/10 px-5 py-2.5 text-sm font-semibold text-accent transition-colors hover:bg-accent/20"
          onClick={() => reset()}
          type="button"
        >
          다시 시도
        </button>
      </div>
    </div>
  );
}
