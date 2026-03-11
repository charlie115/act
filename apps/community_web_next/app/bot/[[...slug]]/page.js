import { redirect } from "next/navigation";

import BotWorkspaceClient from "../../../components/bot/BotWorkspaceClient";
import RequireAuth from "../../../components/auth/RequireAuth";
import { buildMetadata } from "../../../lib/site";

export const metadata = buildMetadata({
  title: "Bot",
  description: "트레이딩 봇 콘솔, 입출금, 트리거, 설정, 조회 탭을 Next 앱에서 제공합니다.",
  pathname: "/bot",
});

const tabs = [
  { key: "triggers", label: "Triggers" },
  { key: "scanner", label: "Scanner" },
  { key: "position", label: "Position" },
  { key: "capital", label: "Capital" },
  { key: "pnl-history", label: "PnL History" },
  { key: "settings", label: "BOT Settings" },
  { key: "api-key", label: "API Key Settings" },
  { key: "deposit", label: "Deposit / Withdrawal" },
];

export default async function BotPage({ params, searchParams }) {
  const resolvedParams = await params;
  const resolvedSearchParams = await searchParams;
  const slug = resolvedParams?.slug || [];
  const currentTab = slug[0] || null;
  const initialConfigUuid = resolvedSearchParams?.config || null;

  if (!currentTab) {
    redirect("/bot/deposit");
  }

  return (
    <RequireAuth>
      <BotWorkspaceClient currentTab={currentTab} initialConfigUuid={initialConfigUuid} />
    </RequireAuth>
  );
}
