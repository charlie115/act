"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import Chip from "@mui/material/Chip";
import Skeleton from "@mui/material/Skeleton";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";

import { alpha, styled } from "@mui/material/styles";

import { useAuth } from "../auth/AuthProvider";

const BalanceChip = styled(Chip)(({ theme }) => ({
  height: 36,
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(theme.palette.primary?.main || "#007cff", 0.12),
  color: theme.palette.primary.main,
  cursor: "pointer",
  fontWeight: theme.typography.fontWeightMedium,
  transition: theme.transitions.create(["background-color", "transform"], {
    duration: theme.transitions.duration.short,
  }),
  "& .MuiChip-icon": {
    color: theme.palette.primary.main,
  },
  "&:hover": {
    backgroundColor: alpha(theme.palette.primary?.main || "#007cff", 0.18),
    transform: "translateY(-1px)",
  },
}));

export default function NextDepositBalance() {
  const router = useRouter();
  const { authorizedListRequest, user } = useAuth();
  const [depositBalances, setDepositBalances] = useState([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadBalance() {
      try {
        const nextDepositBalances = await authorizedListRequest("/users/deposit-balance/");
        if (!active) {
          return;
        }
        setDepositBalances(nextDepositBalances);
        setLoaded(true);
      } catch {
        if (!active) {
          return;
        }
        setDepositBalances([]);
        setLoaded(true);
      }
    }

    loadBalance();
    const intervalId = window.setInterval(loadBalance, 5000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, [authorizedListRequest]);

  const ownBalance = useMemo(
    () => depositBalances.find((item) => item.user === user?.uuid)?.balance ?? null,
    [depositBalances, user?.uuid]
  );

  if (!loaded) {
    return <Skeleton sx={{ borderRadius: 2 }} variant="rounded" width={132} height={36} />;
  }

  return (
    <BalanceChip
      icon={<AccountBalanceWalletIcon />}
      label={`${new Intl.NumberFormat("en-US", {
        maximumFractionDigits: 2,
        minimumFractionDigits: 2,
      }).format(parseFloat(ownBalance || 0))} USDT`}
      onClick={() => router.push("/bot/deposit")}
      size="medium"
    />
  );
}
