"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "../auth/AuthProvider";
import TelegramConnectButton from "../auth/TelegramConnectButton";
import BotApiKeyClient from "./BotApiKeyClient";
import BotCapitalClient from "./BotCapitalClient";
import BotDepositClient from "./BotDepositClient";
import BotPlaceholderPanel from "./BotPlaceholderPanel";
import BotPnlHistoryClient from "./BotPnlHistoryClient";
import BotPositionClient from "./BotPositionClient";
import BotScannerClient from "./BotScannerClient";
import BotSettingsClient from "./BotSettingsClient";
import BotTriggersClient from "./BotTriggersClient";
import BotVolatilityNotificationsClient from "./BotVolatilityNotificationsClient";

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

function isSpotMarket(marketCode) {
  return marketCode?.includes("_SPOT/");
}

export default function BotWorkspaceClient({ currentTab, initialConfigUuid }) {
  const router = useRouter();
  const { user } = useAuth();

  const tradeConfigs = useMemo(
    () => user?.trade_config_allocations || [],
    [user?.trade_config_allocations]
  );

  const selectedConfig = useMemo(() => {
    if (initialConfigUuid === "ALL") {
      return { trade_config_uuid: "ALL" };
    }

    if (!tradeConfigs.length) {
      return null;
    }

    return (
      tradeConfigs.find((item) => item.trade_config_uuid === initialConfigUuid) ||
      tradeConfigs[0]
    );
  }, [initialConfigUuid, tradeConfigs]);

  function buildHref(tabKey) {
    const config = selectedConfig?.trade_config_uuid;
    return config ? `/bot/${tabKey}?config=${config}` : `/bot/${tabKey}`;
  }

  function renderContent() {
    if (currentTab === "deposit") {
      return <BotDepositClient />;
    }

    if (currentTab === "settings" && selectedConfig?.trade_config_uuid === "ALL") {
      return <BotVolatilityNotificationsClient />;
    }

    if (!selectedConfig) {
      return (
        <BotPlaceholderPanel
          title="Trade Config 없음"
          description="사용자에게 할당된 trade config가 없어 읽기 전용 봇 데이터를 불러올 수 없습니다."
        />
      );
    }

    const marketCodeCombination = {
      tradeConfigUuid: selectedConfig.trade_config_uuid,
      target: {
        value: selectedConfig.target_market_code,
        isSpot: isSpotMarket(selectedConfig.target_market_code),
      },
      origin: {
        value: selectedConfig.origin_market_code,
        isSpot: isSpotMarket(selectedConfig.origin_market_code),
      },
    };

    if (currentTab === "position") {
      return <BotPositionClient marketCodeCombination={marketCodeCombination} />;
    }

    if (currentTab === "capital") {
      return <BotCapitalClient marketCodeCombination={marketCodeCombination} />;
    }

    if (currentTab === "pnl-history") {
      return <BotPnlHistoryClient marketCodeCombination={marketCodeCombination} />;
    }

    if (currentTab === "scanner") {
      return <BotScannerClient selectedConfig={selectedConfig} />;
    }

    if (currentTab === "api-key") {
      return (
        <BotApiKeyClient
          marketCodeCombination={marketCodeCombination}
          selectedConfig={selectedConfig}
        />
      );
    }

    if (currentTab === "settings") {
      return (
        <BotSettingsClient
          marketCodeCombination={marketCodeCombination}
          selectedConfig={selectedConfig}
        />
      );
    }

    if (currentTab === "triggers") {
      return <BotTriggersClient selectedConfig={selectedConfig} />;
    }

    return (
      <BotPlaceholderPanel
        title={`${tabs.find((item) => item.key === currentTab)?.label || "Bot"} 이전 중`}
        description="이 탭은 아직 레거시 CRA 구현을 사용합니다. 현재는 입출금, 포지션, 자본, 손익 내역만 Next 앱으로 이전되었습니다."
      />
    );
  }

  return (
    <div className="section-stack">
      {!user?.telegram_chat_id ? (
        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Telegram</p>
              <h1>봇 사용 전 텔레그램 연결이 필요합니다.</h1>
            </div>
          </div>
          <div className="inline-note">
            트리거 생성, 알림, 자동매매 운영 UX를 기존과 같게 유지하려면 텔레그램 계정을 먼저 연결해야 합니다.
          </div>
          <div className="modal-card__actions">
            <TelegramConnectButton />
          </div>
        </section>
      ) : null}
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
                href={buildHref(tab.key)}
              >
                {tab.label}
              </Link>
            ))}
          </div>
        </div>
        <div className="section-heading">
          <div>
            <p className="eyebrow">Trade Config</p>
            <h2>조회 대상 선택</h2>
          </div>
          <select
            className="select-input"
            onChange={(event) => {
              router.replace(`/bot/${currentTab}?config=${event.target.value}`);
            }}
            value={selectedConfig?.trade_config_uuid || ""}
          >
            {currentTab === "settings" ? <option value="ALL">ALL</option> : null}
            {tradeConfigs.length ? (
              tradeConfigs.map((config) => (
                <option key={config.trade_config_uuid} value={config.trade_config_uuid}>
                  {config.target_market_code} : {config.origin_market_code}
                </option>
              ))
            ) : (
              <option value="">No trade configs</option>
            )}
          </select>
        </div>
      </section>
      {user?.telegram_chat_id ? renderContent() : null}
    </div>
  );
}
