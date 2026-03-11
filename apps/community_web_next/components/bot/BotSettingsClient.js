"use client";

import { useEffect, useState } from "react";

import { useAuth } from "../auth/AuthProvider";

function Section({ children, title }) {
  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Settings</p>
          <h2>{title}</h2>
        </div>
      </div>
      {children}
    </section>
  );
}

export default function BotSettingsClient({ marketCodeCombination, selectedConfig }) {
  const { authorizedRequest } = useAuth();
  const [tradeConfig, setTradeConfig] = useState(null);
  const [pageError, setPageError] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [form, setForm] = useState(null);

  useEffect(() => {
    let active = true;

    async function loadConfig() {
      setPageError("");

      try {
        const payload = await authorizedRequest(
          `/tradecore/trade-config/${selectedConfig.trade_config_uuid}/`
        );

        if (!active) {
          return;
        }

        setTradeConfig(payload);
        setForm({
          send_times: payload.send_times ?? 0,
          send_term: payload.send_term ?? 0,
          safe_reverse: Boolean(payload.safe_reverse),
          repeat_limit_p: payload.repeat_limit_p ?? 0,
          on_off: payload.on_off ?? true,
          target_market_cross: payload.target_market_cross ?? false,
          origin_market_cross: payload.origin_market_cross ?? false,
          target_market_leverage: payload.target_market_leverage ?? 1,
          origin_market_leverage: payload.origin_market_leverage ?? 1,
          target_market_margin_call: payload.target_market_margin_call ?? "",
          origin_market_margin_call: payload.origin_market_margin_call ?? "",
        });
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load bot settings.");
      }
    }

    loadConfig();

    return () => {
      active = false;
    };
  }, [authorizedRequest, selectedConfig.trade_config_uuid]);

  if (!form || !tradeConfig) {
    return (
      <Section title="봇 설정">
        <div className="inline-note">설정을 불러오는 중입니다.</div>
        {pageError ? <p className="auth-card__error">{pageError}</p> : null}
      </Section>
    );
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsBusy(true);
    setPageError("");

    try {
      const payload = {
        uuid: tradeConfig.uuid,
        user: tradeConfig.user,
        telegram_id: tradeConfig.telegram_id,
        target_market_code: tradeConfig.target_market_code,
        origin_market_code: tradeConfig.origin_market_code,
        send_times: Number(form.send_times),
        send_term: Number(form.send_term),
        safe_reverse: Boolean(form.safe_reverse),
        repeat_limit_p: Number(form.repeat_limit_p),
        on_off: Boolean(form.on_off),
      };

      if (!marketCodeCombination.target.isSpot) {
        payload.target_market_cross = Boolean(form.target_market_cross);
        payload.target_market_leverage = Number(form.target_market_leverage);
        payload.target_market_margin_call =
          form.target_market_margin_call === "" ? null : Number(form.target_market_margin_call);
      }

      if (!marketCodeCombination.origin.isSpot) {
        payload.origin_market_cross = Boolean(form.origin_market_cross);
        payload.origin_market_leverage = Number(form.origin_market_leverage);
        payload.origin_market_margin_call =
          form.origin_market_margin_call === "" ? null : Number(form.origin_market_margin_call);
      }

      const updated = await authorizedRequest(`/tradecore/trade-config/${tradeConfig.uuid}/`, {
        method: "PUT",
        body: payload,
      });

      setTradeConfig(updated);
    } catch (requestError) {
      setPageError(requestError.message || "Failed to update bot settings.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <Section title="봇 설정">
      <form className="auth-form" onSubmit={handleSubmit}>
        <div className="two-column-grid">
          <div className="auth-form">
            <label className="auth-form__field" htmlFor="send-times">
              Telegram Message Alarm Count
            </label>
            <input
              className="auth-form__input"
              id="send-times"
              min="0"
              onChange={(event) => setForm((current) => ({ ...current, send_times: event.target.value }))}
              type="number"
              value={form.send_times}
            />

            <label className="auth-form__field" htmlFor="send-term">
              Telegram Message Interval
            </label>
            <input
              className="auth-form__input"
              id="send-term"
              min="0"
              onChange={(event) => setForm((current) => ({ ...current, send_term: event.target.value }))}
              type="number"
              value={form.send_term}
            />

            <label className="checkbox-row">
              <input
                checked={form.safe_reverse}
                onChange={(event) => setForm((current) => ({ ...current, safe_reverse: event.target.checked }))}
                type="checkbox"
              />
              <span>Safe Reverse</span>
            </label>

            <label className="checkbox-row">
              <input
                checked={form.on_off}
                onChange={(event) => setForm((current) => ({ ...current, on_off: event.target.checked }))}
                type="checkbox"
              />
              <span>Bot Enabled</span>
            </label>

            <label className="auth-form__field" htmlFor="repeat-limit">
              Repeat Limit (%)
            </label>
            <input
              className="auth-form__input"
              id="repeat-limit"
              onChange={(event) => setForm((current) => ({ ...current, repeat_limit_p: event.target.value }))}
              step="0.001"
              type="number"
              value={form.repeat_limit_p}
            />
          </div>

          <div className="auth-form">
            {!marketCodeCombination.target.isSpot ? (
              <div className="inline-note">
                <strong>{marketCodeCombination.target.value}</strong>
                <div className="auth-form">
                  <label className="checkbox-row">
                    <input
                      checked={form.target_market_cross}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          target_market_cross: event.target.checked,
                        }))
                      }
                      type="checkbox"
                    />
                    <span>Cross Margin</span>
                  </label>
                  <input
                    className="auth-form__input"
                    min="1"
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        target_market_leverage: event.target.value,
                      }))
                    }
                    placeholder="Leverage"
                    type="number"
                    value={form.target_market_leverage}
                  />
                  <input
                    className="auth-form__input"
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        target_market_margin_call: event.target.value,
                      }))
                    }
                    placeholder="Liquidation Detection Mode"
                    type="number"
                    value={form.target_market_margin_call}
                  />
                </div>
              </div>
            ) : (
              <div className="inline-note">
                {marketCodeCombination.target.value} is a SPOT market. Separate futures settings are not required.
              </div>
            )}

            {!marketCodeCombination.origin.isSpot ? (
              <div className="inline-note">
                <strong>{marketCodeCombination.origin.value}</strong>
                <div className="auth-form">
                  <label className="checkbox-row">
                    <input
                      checked={form.origin_market_cross}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          origin_market_cross: event.target.checked,
                        }))
                      }
                      type="checkbox"
                    />
                    <span>Cross Margin</span>
                  </label>
                  <input
                    className="auth-form__input"
                    min="1"
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        origin_market_leverage: event.target.value,
                      }))
                    }
                    placeholder="Leverage"
                    type="number"
                    value={form.origin_market_leverage}
                  />
                  <input
                    className="auth-form__input"
                    onChange={(event) =>
                      setForm((current) => ({
                        ...current,
                        origin_market_margin_call: event.target.value,
                      }))
                    }
                    placeholder="Liquidation Detection Mode"
                    type="number"
                    value={form.origin_market_margin_call}
                  />
                </div>
              </div>
            ) : (
              <div className="inline-note">
                {marketCodeCombination.origin.value} is a SPOT market. Separate futures settings are not required.
              </div>
            )}
          </div>
        </div>

        <button className="primary-button ghost-button--button auth-button" disabled={isBusy} type="submit">
          {isBusy ? "Saving..." : "Save Settings"}
        </button>
      </form>
      {pageError ? <p className="auth-card__error">{pageError}</p> : null}
    </Section>
  );
}
