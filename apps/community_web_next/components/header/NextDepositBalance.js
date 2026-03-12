"use client";

import { useRouter } from "next/navigation";

import Chip from "@mui/material/Chip";
import Skeleton from "@mui/material/Skeleton";
import AccountBalanceWalletIcon from "@mui/icons-material/AccountBalanceWallet";

import { useSelector } from "react-redux";
import { alpha, styled } from "@mui/material/styles";

import { useGetDepositBalanceQuery } from "redux/api/drf/user";
import formatIntlNumber from "utils/formatIntlNumber";

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
  const { user } = useSelector((state) => state.auth);

  const { data, isSuccess } = useGetDepositBalanceQuery({}, { pollingInterval: 5000 });

  const ownBalance =
    data?.results?.find((item) => item.user === user?.uuid)?.balance ?? null;

  if (!isSuccess) {
    return <Skeleton sx={{ borderRadius: 2 }} variant="rounded" width={132} height={36} />;
  }

  return (
    <BalanceChip
      icon={<AccountBalanceWalletIcon />}
      label={`${formatIntlNumber(parseFloat(ownBalance || 0), 2, 2)} USDT`}
      onClick={() => router.push("/bot/deposit")}
      size="medium"
    />
  );
}
