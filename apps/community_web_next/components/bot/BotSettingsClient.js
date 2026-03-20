"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useAuth } from "../auth/AuthProvider";
import BotVolatilityNotificationsClient from "./BotVolatilityNotificationsClient";

function Toggle({ value, onChange, labelOn = "교차", labelOff = "격리" }) {
  return (
    <button
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        value ? "bg-accent" : "bg-border"
      }`}
      onClick={() => onChange(!value)}
      type="button"
    >
      <span
        className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
          value ? "translate-x-5.5" : "translate-x-1"
        }`}
      />
      <span className="sr-only">{value ? labelOn : labelOff}</span>
    </button>
  );
}

function FieldWrapper({ label, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium text-ink-muted">{label}</label>
      {children}
    </div>
  );
}

function NumberInput({ value, onChange, min, max, placeholder }) {
  return (
    <input
      className="rounded-lg border border-border bg-background/80 px-3 py-2 text-sm text-ink outline-none focus:border-accent/40"
      max={max}
      min={min}
      onChange={(e) => onChange(Number(e.target.value))}
      placeholder={placeholder}
      type="number"
      value={value ?? ""}
    />
  );
}

function ToggleField({ label, value, onChange, labelOn, labelOff }) {
  return (
    <FieldWrapper label={label}>
      <div className="flex items-center gap-2">
        <Toggle labelOff={labelOff} labelOn={labelOn} onChange={onChange} value={value} />
        <span className="text-xs text-ink-muted">
          {value ? (labelOn || "ON") : (labelOff || "OFF")}
        </span>
      </div>
    </FieldWrapper>
  );
}

export default function BotSettingsClient({
  marketCodeCombination,
  selectedConfig,
  marketCodeSelectorRef,
}) {
  const { authorizedRequest } = useAuth();
  const [config, setConfig] = useState(null);
  const [fetchedUuid, setFetchedUuid] = useState(null);
  const [formData, setFormData] = useState({});

  const currentUuid = selectedConfig?.trade_config_uuid;
  const loading =
    currentUuid && currentUuid !== "ALL" && fetchedUuid !== currentUuid;

  useEffect(() => {
    if (!currentUuid || currentUuid === "ALL") return;
    let active = true;
    authorizedRequest(`/tradecore/trade-config/${currentUuid}/`)
      .then((data) => {
        if (active) {
          setConfig(data);
          setFormData({
            send_times: data.send_times ?? 0,
            send_term: data.send_term ?? 0,
            target_market_leverage: data.target_market_leverage ?? 1,
            origin_market_leverage: data.origin_market_leverage ?? 1,
            target_market_cross: data.target_market_cross ?? false,
            origin_market_cross: data.origin_market_cross ?? false,
            safe_reverse: data.safe_reverse ?? false,
            on_off: data.on_off ?? false,
          });
          setFetchedUuid(currentUuid);
        }
      })
      .catch(() => {
        if (active) {
          setConfig(null);
          setFetchedUuid(currentUuid);
        }
      });
    return () => {
      active = false;
    };
  }, [currentUuid, authorizedRequest]);

  function updateField(key, value) {
    setFormData((prev) => ({ ...prev, [key]: value }));
  }

  async function handleSave() {
    try {
      await authorizedRequest(
        `/tradecore/trade-config/${selectedConfig.trade_config_uuid}/`,
        {
          method: "PUT",
          body: formData,
        },
      );
      toast.success("설정 저장 완료");
    } catch {
      toast.error("저장 실패");
    }
  }

  // Mode A — "ALL" selected: show volatility notification settings
  if (!selectedConfig || selectedConfig.value === "ALL") {
    return (
      <BotVolatilityNotificationsClient
        marketCodeSelectorRef={marketCodeSelectorRef}
      />
    );
  }

  // Mode B — specific market code selected
  if (loading) {
    return (
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">봇 설정</h3>
        <p className="py-8 text-center text-sm text-ink-muted">
          설정을 불러오는 중...
        </p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-ink">봇 설정</h3>
        <p className="py-8 text-center text-sm text-ink-muted">
          설정 정보를 불러올 수 없습니다.
        </p>
      </div>
    );
  }

  const targetIsSpot = selectedConfig.target?.isSpot;
  const originIsSpot = selectedConfig.origin?.isSpot;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-ink">봇 설정</h3>

      <div className="rounded-lg border border-border bg-background/90 p-4 sm:p-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-6">
          {/* Telegram settings */}
          <FieldWrapper label="Telegram 알림 횟수">
            <NumberInput
              min={0}
              onChange={(v) => updateField("send_times", v)}
              value={formData.send_times}
            />
          </FieldWrapper>

          <FieldWrapper label="Telegram 알림 간격 (분)">
            <NumberInput
              min={0}
              onChange={(v) => updateField("send_term", v)}
              value={formData.send_term}
            />
          </FieldWrapper>

          {/* Leverage — target */}
          {!targetIsSpot && (
            <FieldWrapper label="레버리지 - 타겟">
              <NumberInput
                max={20}
                min={1}
                onChange={(v) => updateField("target_market_leverage", v)}
                value={formData.target_market_leverage}
              />
            </FieldWrapper>
          )}

          {/* Leverage — origin */}
          {!originIsSpot && (
            <FieldWrapper label="레버리지 - 오리진">
              <NumberInput
                max={20}
                min={1}
                onChange={(v) => updateField("origin_market_leverage", v)}
                value={formData.origin_market_leverage}
              />
            </FieldWrapper>
          )}

          {/* Margin mode — target */}
          {!targetIsSpot && (
            <ToggleField
              label="마진 모드 - 타겟"
              labelOff="격리"
              labelOn="교차"
              onChange={(v) => updateField("target_market_cross", v)}
              value={formData.target_market_cross}
            />
          )}

          {/* Margin mode — origin */}
          {!originIsSpot && (
            <ToggleField
              label="마진 모드 - 오리진"
              labelOff="격리"
              labelOn="교차"
              onChange={(v) => updateField("origin_market_cross", v)}
              value={formData.origin_market_cross}
            />
          )}

          {/* Safe reverse */}
          <ToggleField
            label="안전 역전환"
            labelOff="OFF"
            labelOn="ON"
            onChange={(v) => updateField("safe_reverse", v)}
            value={formData.safe_reverse}
          />

          {/* On/Off */}
          <ToggleField
            label="온/오프"
            labelOff="OFF"
            labelOn="ON"
            onChange={(v) => updateField("on_off", v)}
            value={formData.on_off}
          />
        </div>

        {/* Save button */}
        <div className="mt-6 flex justify-end">
          <button
            className="rounded-lg bg-accent px-6 py-2 text-sm text-white transition-colors hover:bg-accent/90"
            onClick={handleSave}
            type="button"
          >
            저장
          </button>
        </div>
      </div>
    </div>
  );
}
