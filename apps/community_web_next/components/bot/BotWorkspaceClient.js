"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowLeftRight,
  ChevronRight,
  Crosshair,
  History,
  Key,
  LayoutGrid,
  MessageCircle,
  ScanLine,
  Settings,
  Wallet,
} from "lucide-react";

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
  { key: "triggers", label: "트리거", icon: Crosshair },
  { key: "scanner", label: "스캐너", icon: ScanLine },
  { key: "position", label: "포지션", icon: Activity },
  { key: "capital", label: "자본", icon: LayoutGrid },
  { key: "pnl-history", label: "손익", icon: History },
  { key: "settings", label: "설정", icon: Settings },
  { key: "api-key", label: "API 키", icon: Key },
  { key: "deposit", label: "입출금", icon: Wallet },
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

  const activeTab = tabs.find((t) => t.key === currentTab);

  return (
    <div className="grid gap-4">
      {/* Telegram connect banner */}
      {!user?.telegram_chat_id ? (
        <div className="flex flex-col gap-3 rounded-lg border border-amber-500/20 bg-amber-950/20 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="mb-1 flex items-center gap-2">
              <MessageCircle size={16} strokeWidth={2} className="text-amber-400" />
              <span className="text-sm font-bold text-ink">텔레그램 연결 필요</span>
            </div>
            <p className="text-[0.78rem] leading-relaxed text-ink-muted">
              트리거 알림, 자동매매 운영을 위해 텔레그램을 먼저 연결해주세요.
            </p>
          </div>
          <TelegramConnectButton />
        </div>
      ) : null}

      {/* Tab bar + Market selector */}
      <div className="rounded-lg border border-border bg-background/92 overflow-hidden">
        {/* Tab navigation */}
        <div className="flex items-center gap-1 overflow-x-auto border-b border-border/50 px-3 py-2">
          {tabs.map((tab) => {
            const active = currentTab === tab.key;
            const Icon = tab.icon;
            return (
              <Link
                key={tab.key}
                className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3 py-1.5 text-[0.74rem] font-semibold transition-all ${
                  active
                    ? "bg-accent/15 text-accent shadow-sm"
                    : "text-ink-muted hover:bg-surface-elevated/50 hover:text-ink"
                }`}
                href={buildHref(tab.key)}
              >
                <Icon size={14} strokeWidth={2} />
                {tab.label}
              </Link>
            );
          })}
        </div>

        {/* Market code selector row */}
        <div className="flex items-center justify-between gap-3 px-4 py-2.5 bg-surface-elevated/10">
          <div className="flex items-center gap-2 text-[0.72rem] text-ink-muted">
            <ArrowLeftRight size={14} strokeWidth={2} className="text-accent/60" />
            <span>거래 대상</span>
          </div>
          <BotMarketCodeCombinationSelector
            ref={marketCodeSelectorRef}
            buttonStyle={{ minWidth: 280 }}
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
      </div>

      {/* Content area */}
      {user?.telegram_chat_id ? (
        <div className="rounded-lg border border-border bg-background/92">
          {renderContent()}
        </div>
      ) : null}
    </div>
  );
}
