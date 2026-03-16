"use client";

import { useEffect, useState } from "react";
import { Wallet } from "lucide-react";
import { useAuth } from "../auth/AuthProvider";

export default function NextDepositBalance() {
  const { loggedIn, authorizedRequest } = useAuth();
  const [balance, setBalance] = useState(null);

  useEffect(() => {
    if (!loggedIn) return;
    authorizedRequest("/users/deposit-balance/")
      .then((data) => {
        const results = Array.isArray(data) ? data : data?.results || [];
        if (results.length > 0) setBalance(results[0]?.balance);
      })
      .catch(() => {});
  }, [loggedIn, authorizedRequest]);

  if (!loggedIn || balance === null) return null;

  return (
    <div className="flex items-center gap-1.5 rounded-lg bg-surface-elevated/60 px-3 py-1.5 text-xs text-ink-muted">
      <Wallet size={12} />
      <span>{Number(balance).toLocaleString()} USDT</span>
    </div>
  );
}
