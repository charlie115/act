import Link from "next/link";
import { redirect } from "next/navigation";

import BotDepositClient from "../../../components/bot/BotDepositClient";
import BotPlaceholderPanel from "../../../components/bot/BotPlaceholderPanel";
import RequireAuth from "../../../components/auth/RequireAuth";
import { buildMetadata } from "../../../lib/site";

export const metadata = buildMetadata({
  title: "Bot",
  description: "봇 영역은 단계적으로 Next 앱으로 이전 중이며, 입출금 화면은 실제 동작합니다.",
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

function renderBotContent(currentTab) {
  if (currentTab === "deposit") {
    return <BotDepositClient />;
  }

  return (
    <BotPlaceholderPanel
      title={`${tabs.find((item) => item.key === currentTab)?.label || "Bot"} 이전 중`}
      description="이 탭은 아직 레거시 CRA 구현을 사용합니다. 현재는 입출금 플로우만 Next 앱으로 실제 이전되었습니다."
    />
  );
}

export default function BotPage({ params }) {
  const slug = params?.slug || [];
  const currentTab = slug[0] || null;

  if (!currentTab) {
    redirect("/bot/deposit");
  }

  return (
    <RequireAuth>
      <div className="section-stack">
        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Bot</p>
              <h1>트레이딩 봇 콘솔</h1>
            </div>
            <div className="tab-strip">
              {tabs.map((tab) => (
                <Link
                  key={tab.key}
                  className={`tab-pill${currentTab === tab.key ? " tab-pill--active" : ""}`}
                  href={`/bot/${tab.key}`}
                >
                  {tab.label}
                </Link>
              ))}
            </div>
          </div>
        </section>
        {renderBotContent(currentTab)}
      </div>
    </RequireAuth>
  );
}
