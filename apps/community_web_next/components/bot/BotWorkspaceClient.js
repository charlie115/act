"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import Box from "@mui/material/Box";
import CheckBoxIcon from "@mui/icons-material/CheckBox";
import IconButton from "@mui/material/IconButton";
import AddIcon from "@mui/icons-material/Add";

import sortBy from "lodash/sortBy";
import uniqBy from "lodash/uniqBy";

import { useAuth } from "../auth/AuthProvider";
import TelegramConnectButton from "../auth/TelegramConnectButton";
import BotApiKeyClient from "./BotApiKeyClient";
import BotCapitalClient from "./BotCapitalClient";
import BotDepositClient from "./BotDepositClient";
import BotMarketCodeCombinationSelector from "./BotMarketCodeCombinationSelector";
import BotPlaceholderPanel from "./BotPlaceholderPanel";
import BotPnlHistoryClient from "./BotPnlHistoryClient";
import BotPositionClient from "./BotPositionClient";
import BotScannerClient from "./BotScannerClient";
import BotSettingsClient from "./BotSettingsClient";
import BotTriggersClient from "./BotTriggersClient";
import { getMarketOption } from "../../lib/markets";

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

const MARKET_CODES_REQUIRED = ["settings", "position", "capital"];
const TRADE_SUPPORT_REQUIRED = ["position", "capital", "pnl-history", "api-key"];

export default function BotWorkspaceClient({ currentTab, initialConfigUuid }) {
  const marketCodeSelectorRef = useRef(null);
  const router = useRouter();
  const { authorizedListRequest, user } = useAuth();
  const [nodes, setNodes] = useState([]);

  const tradeConfigs = useMemo(
    () => user?.trade_config_allocations || [],
    [user?.trade_config_allocations]
  );

  const tradeConfigAllocations = useMemo(
    () =>
      tradeConfigs.map((tradeConfig) => {
        const target = getMarketOption(tradeConfig.target_market_code);
        const origin = getMarketOption(tradeConfig.origin_market_code);

        return {
          node: tradeConfig.node,
          origin,
          target,
          tradeSupport: true,
          trade_config_uuid: tradeConfig.trade_config_uuid,
          uuid: tradeConfig.trade_config_uuid,
          value: `${tradeConfig.target_market_code}:${tradeConfig.origin_market_code}`,
        };
      }),
    [tradeConfigs]
  );

  const tradeConfigUuids = useMemo(
    () => tradeConfigs.map((tradeConfig) => tradeConfig.trade_config_uuid),
    [tradeConfigs]
  );

  useEffect(() => {
    let active = true;

    async function loadNodes() {
      try {
        const payload = await authorizedListRequest("/tradecore/nodes/");
        if (active) {
          setNodes(payload?.results || payload || []);
        }
      } catch {
        if (active) {
          setNodes([]);
        }
      }
    }

    loadNodes();

    return () => {
      active = false;
    };
  }, [authorizedListRequest]);

  const marketCodeCombinationList = useMemo(() => {
    if (!nodes.length) {
      return [];
    }

    const nodeMarketCodes = nodes.reduce(
      (accumulator, currentNode) =>
        accumulator.concat(
          currentNode.market_code_combinations?.map((item) => ({
            marketCodeCombination: item.market_code_combination,
            tradeSupport: item.trade_support,
            ...currentNode,
          })) || []
        ),
      []
    );

    const uniqNodeMarketCodes = uniqBy(nodeMarketCodes, "marketCodeCombination");
    return [
      {
        getLabel: () => "All",
        icon: <CheckBoxIcon sx={{ verticalAlign: "middle" }} />,
        value: "ALL",
      },
      ...sortBy(
        uniqNodeMarketCodes.map((item) => {
          const [targetMarket, originMarket] = item.marketCodeCombination.split(":");
          const target = getMarketOption(targetMarket);
          const origin = getMarketOption(originMarket);
          const tradeConfigAllocation = tradeConfigs.find(
            (tradeConfig) =>
              tradeConfig.target_market_code === targetMarket &&
              tradeConfig.origin_market_code === originMarket
          );

          return {
            ...item,
            disabled:
              !tradeConfigAllocation?.trade_config_uuid ||
              (TRADE_SUPPORT_REQUIRED.includes(currentTab) && !item.tradeSupport),
            origin: {
              ...origin,
              isSpot: originMarket.includes("SPOT"),
            },
            secondaryIcon: !tradeConfigAllocation?.trade_config_uuid ? (
              <IconButton
                color="success"
                edge="end"
                onClick={(event) => {
                  event.stopPropagation();
                }}
                sx={{ p: 0 }}
              >
                <AddIcon sx={{ fontSize: 20 }} />
              </IconButton>
            ) : null,
            target: {
              ...target,
              isSpot: targetMarket.includes("SPOT"),
            },
            trade_config_uuid: tradeConfigAllocation?.trade_config_uuid,
            value: item.marketCodeCombination,
          };
        }),
        "trade_config_uuid"
      ),
    ];
  }, [currentTab, nodes, tradeConfigs]);

  const selectedConfig = useMemo(() => {
    if (initialConfigUuid === "ALL" && currentTab === "settings") {
      return (
        marketCodeCombinationList.find((item) => item.value === "ALL") || {
          trade_config_uuid: "ALL",
          value: "ALL",
        }
      );
    }

    const optionsWithConfig = marketCodeCombinationList.filter(
      (item) => item.trade_config_uuid
    );

    if (!optionsWithConfig.length) {
      return null;
    }

    return (
      optionsWithConfig.find((item) => item.trade_config_uuid === initialConfigUuid) ||
      optionsWithConfig[0]
    );
  }, [currentTab, initialConfigUuid, marketCodeCombinationList]);

  useEffect(() => {
    if (
      MARKET_CODES_REQUIRED.includes(currentTab) &&
      currentTab !== "settings" &&
      (!selectedConfig || selectedConfig.value === "ALL")
    ) {
      marketCodeSelectorRef.current?.open?.();
    }
  }, [currentTab, selectedConfig]);

  function buildHref(tabKey) {
    if (selectedConfig?.trade_config_uuid === "ALL" && tabKey !== "settings") {
      return `/bot/${tabKey}`;
    }

    const config = selectedConfig?.trade_config_uuid;
    return config ? `/bot/${tabKey}?config=${config}` : `/bot/${tabKey}`;
  }

  function renderContent() {
    const marketCodeCombination =
      selectedConfig && selectedConfig.value !== "ALL"
        ? {
            ...selectedConfig,
            tradeConfigUuid: selectedConfig.tradeConfigUuid || selectedConfig.trade_config_uuid,
          }
        : selectedConfig || {};

    if (currentTab === "deposit") {
      return <BotDepositClient />;
    }

    if (currentTab === "settings" && selectedConfig?.trade_config_uuid === "ALL") {
      return (
        <BotSettingsClient
          marketCodeCombination={selectedConfig}
          selectedConfig={selectedConfig}
          marketCodeSelectorRef={marketCodeSelectorRef}
        />
      );
    }

    if (!selectedConfig) {
      return (
        <BotPlaceholderPanel
          title="Trade Config 없음"
          description="사용자에게 할당된 trade config가 없어 읽기 전용 봇 데이터를 불러올 수 없습니다."
        />
      );
    }

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
      return (
        <BotScannerClient selectedConfig={selectedConfig} />
      );
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
          marketCodeSelectorRef={marketCodeSelectorRef}
        />
      );
    }

    if (currentTab === "triggers") {
      return <BotTriggersClient selectedConfig={selectedConfig} />;
    }

    return (
        <BotPlaceholderPanel
          title={`${tabs.find((item) => item.key === currentTab)?.label || "Bot"} 이전 중`}
          description="이 탭은 아직 레거시 CRA 구현 전체를 다 옮기지 못했습니다."
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
          <BotMarketCodeCombinationSelector
            ref={marketCodeSelectorRef}
            buttonStyle={{ minWidth: 320 }}
            marketCodesRequired={MARKET_CODES_REQUIRED.includes(currentTab) && currentTab !== "settings"}
            onSelectItem={(nextValue) => {
              const nextConfig = nextValue?.trade_config_uuid;
              if (!nextConfig || nextValue.value === "ALL") {
                router.replace(
                  currentTab === "settings" ? `/bot/${currentTab}?config=ALL` : `/bot/${currentTab}`
                );
                return;
              }

              router.replace(`/bot/${currentTab}?config=${nextConfig}`);
            }}
            options={marketCodeCombinationList}
            tradeSupportRequired={TRADE_SUPPORT_REQUIRED.includes(currentTab)}
            value={
              selectedConfig?.trade_config_uuid === "ALL"
                ? marketCodeCombinationList.find((item) => item.value === "ALL") || {
                    getLabel: () => "All",
                    value: "ALL",
                  }
                : selectedConfig
            }
          />
        </div>
      </section>
      {user?.telegram_chat_id ? renderContent() : null}
    </div>
  );
}
