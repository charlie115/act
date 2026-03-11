"use client";

import { useEffect, useState } from "react";

import { useAuth } from "../auth/AuthProvider";

function formatAmount(value, digits = 3) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: digits,
    minimumFractionDigits: 0,
  }).format(Number(value));
}

function emptyTriggerForm() {
  return {
    base_asset: "",
    low: "",
    high: "",
    trade_capital: "100",
    usdt_conversion: false,
  };
}

function emptyRepeatForm() {
  return {
    is_fixed: false,
    kline_num: "200",
    pauto_num: "1",
    auto_repeat_num: "0",
  };
}

export default function BotTriggersClient({ selectedConfig }) {
  const { authorizedListRequest, authorizedRequest } = useAuth();
  const [assets, setAssets] = useState([]);
  const [trades, setTrades] = useState([]);
  const [pageError, setPageError] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [showTriggerModal, setShowTriggerModal] = useState(false);
  const [editingTrade, setEditingTrade] = useState(null);
  const [triggerForm, setTriggerForm] = useState(emptyTriggerForm());
  const [historyTrade, setHistoryTrade] = useState(null);
  const [tradeHistory, setTradeHistory] = useState([]);
  const [repeatTrade, setRepeatTrade] = useState(null);
  const [showRepeatModal, setShowRepeatModal] = useState(false);
  const [repeatForm, setRepeatForm] = useState(emptyRepeatForm());

  useEffect(() => {
    let active = true;

    async function loadPage() {
      setPageError("");

      try {
        const [assetPayload, tradePayload] = await Promise.all([
          fetch("/api/infocore/assets/", { cache: "no-store" }).then((response) => response.json()),
          authorizedListRequest(
            `/tradecore/trades/?trade_config_uuid=${selectedConfig.trade_config_uuid}`
          ),
        ]);

        if (!active) {
          return;
        }

        setAssets(assetPayload?.results || []);
        setTrades(tradePayload);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load triggers.");
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [authorizedListRequest, selectedConfig.trade_config_uuid]);

  async function reloadTrades() {
    const nextTrades = await authorizedListRequest(
      `/tradecore/trades/?trade_config_uuid=${selectedConfig.trade_config_uuid}`
    );
    setTrades(nextTrades);
  }

  function openCreateModal() {
    setEditingTrade(null);
    setTriggerForm(emptyTriggerForm());
    setShowTriggerModal(true);
  }

  function openEditModal(trade) {
    setEditingTrade(trade);
    setTriggerForm({
      base_asset: trade.base_asset,
      low: trade.low,
      high: trade.high,
      trade_capital: trade.trade_capital || "100",
      usdt_conversion: Boolean(trade.usdt_conversion),
    });
    setShowTriggerModal(true);
  }

  async function handleTriggerSubmit(event) {
    event.preventDefault();
    setIsBusy(true);
    setPageError("");

    try {
      const payload = {
        trade_config_uuid: selectedConfig.trade_config_uuid,
        base_asset: triggerForm.base_asset,
        low: Number(triggerForm.low),
        high: Number(triggerForm.high),
        trade_capital: Number(triggerForm.trade_capital),
        usdt_conversion: Boolean(triggerForm.usdt_conversion),
        trigger_switch: 1,
        trade_switch: 1,
      };

      if (editingTrade) {
        await authorizedRequest(`/tradecore/trades/${editingTrade.uuid}/`, {
          method: "PUT",
          body: {
            ...payload,
            uuid: editingTrade.uuid,
          },
        });
      } else {
        await authorizedRequest("/tradecore/trades/", {
          method: "POST",
          body: payload,
        });
      }

      setShowTriggerModal(false);
      setEditingTrade(null);
      setTriggerForm(emptyTriggerForm());
      await reloadTrades();
    } catch (requestError) {
      setPageError(requestError.payload?.detail || requestError.message || "Failed to save trigger.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDelete(item) {
    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest(
        `/tradecore/trades/${item.uuid}/?trade_config_uuid=${selectedConfig.trade_config_uuid}`,
        { method: "DELETE" }
      );
      await reloadTrades();
    } catch (requestError) {
      setPageError(requestError.message || "Failed to delete trigger.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleShowHistory(trade) {
    setIsBusy(true);
    setPageError("");

    try {
      const payload = await authorizedListRequest(
        `/tradecore/trade-history/?trade_config_uuid=${selectedConfig.trade_config_uuid}&trade_uuid=${trade.uuid}`
      );
      setHistoryTrade(trade);
      setTradeHistory(payload);
    } catch (requestError) {
      setPageError(requestError.message || "Failed to load trade history.");
    } finally {
      setIsBusy(false);
    }
  }

  async function openRepeatModal(trade) {
    setIsBusy(true);
    setPageError("");

    try {
      const payload = await authorizedListRequest(
        `/tradecore/repeat-trades/?trade_config_uuid=${selectedConfig.trade_config_uuid}&trade_uuid=${trade.uuid}`
      );
      const repeat = payload[0] || null;

      setRepeatTrade(trade);
      setRepeatForm(
        repeat
          ? {
              is_fixed: repeat.pauto_num === null,
              kline_num: repeat.kline_num || "200",
              pauto_num: repeat.pauto_num || "1",
              auto_repeat_num: repeat.auto_repeat_num || "0",
            }
          : emptyRepeatForm()
      );
      setShowRepeatModal(true);
    } catch (requestError) {
      setPageError(requestError.message || "Failed to load auto-repeat settings.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRepeatSubmit(event) {
    event.preventDefault();

    if (!repeatTrade) {
      return;
    }

    setIsBusy(true);
    setPageError("");

    try {
      const payload = await authorizedListRequest(
        `/tradecore/repeat-trades/?trade_config_uuid=${selectedConfig.trade_config_uuid}&trade_uuid=${repeatTrade.uuid}`
      );
      const existing = payload[0] || null;

      const body = {
        trade_config_uuid: selectedConfig.trade_config_uuid,
        trade_uuid: repeatTrade.uuid,
        auto_repeat_switch: 1,
        auto_repeat_num: Number(repeatForm.auto_repeat_num || 0),
      };

      if (!repeatForm.is_fixed) {
        body.kline_num = Number(repeatForm.kline_num || 200);
        body.pauto_num = Number(repeatForm.pauto_num || 1);
      }

      if (existing) {
        await authorizedRequest(`/tradecore/repeat-trades/${existing.uuid}/`, {
          method: "PUT",
          body: {
            ...body,
            uuid: existing.uuid,
          },
        });
      } else {
        await authorizedRequest("/tradecore/repeat-trades/", {
          method: "POST",
          body,
        });
      }

      setShowRepeatModal(false);
      setRepeatTrade(null);
    } catch (requestError) {
      setPageError(requestError.payload?.detail || requestError.message || "Failed to save auto-repeat settings.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRepeatDisable() {
    if (!repeatTrade) {
      return;
    }

    setIsBusy(true);
    setPageError("");

    try {
      const payload = await authorizedListRequest(
        `/tradecore/repeat-trades/?trade_config_uuid=${selectedConfig.trade_config_uuid}&trade_uuid=${repeatTrade.uuid}`
      );
      const existing = payload[0] || null;

      if (existing) {
        await authorizedRequest(
          `/tradecore/repeat-trades/${existing.uuid}/?trade_config_uuid=${selectedConfig.trade_config_uuid}`,
          { method: "DELETE" }
        );
      }

      setShowRepeatModal(false);
      setRepeatTrade(null);
    } catch (requestError) {
      setPageError(requestError.message || "Failed to disable auto-repeat.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Triggers</p>
            <h1>트리거 관리</h1>
          </div>
          <button className="primary-button ghost-button--button" onClick={openCreateModal} type="button">
            Add Trigger
          </button>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Base Asset</th>
                <th>Entry</th>
                <th>Exit</th>
                <th>Capital</th>
                <th>Status</th>
                <th>Edit</th>
                <th>History</th>
                <th>Auto Repeat</th>
                <th>Delete</th>
              </tr>
            </thead>
            <tbody>
              {trades.length ? (
                trades.map((trade) => (
                  <tr key={trade.uuid}>
                    <td>{trade.base_asset}</td>
                    <td>{formatAmount(trade.low)}</td>
                    <td>{formatAmount(trade.high)}</td>
                    <td>{formatAmount(trade.trade_capital, 0)}</td>
                    <td>{trade.status || "-"}</td>
                    <td>
                      <button
                        className="ghost-button ghost-button--button"
                        onClick={() => openEditModal(trade)}
                        type="button"
                      >
                        Edit
                      </button>
                    </td>
                    <td>
                      <button
                        className="ghost-button ghost-button--button"
                        onClick={() => handleShowHistory(trade)}
                        type="button"
                      >
                        View
                      </button>
                    </td>
                    <td>
                      <button
                        className="ghost-button ghost-button--button"
                        onClick={() => openRepeatModal(trade)}
                        type="button"
                      >
                        Configure
                      </button>
                    </td>
                    <td>
                      <button
                        className="ghost-button ghost-button--button"
                        onClick={() => handleDelete(trade)}
                        type="button"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="9">No triggers configured.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {historyTrade ? (
        <section className="surface-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Trade History</p>
              <h2>{historyTrade.base_asset}</h2>
            </div>
            <button
              className="ghost-button ghost-button--button"
              onClick={() => {
                setHistoryTrade(null);
                setTradeHistory([]);
              }}
              type="button"
            >
              Close
            </button>
          </div>
          <div className="table-shell">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Registered</th>
                  <th>Side</th>
                  <th>Executed Premium</th>
                  <th>Slippage</th>
                  <th>Trade UUID</th>
                </tr>
              </thead>
              <tbody>
                {tradeHistory.length ? (
                  tradeHistory.map((item) => (
                    <tr key={item.uuid}>
                      <td>{new Date(item.registered_datetime).toLocaleString()}</td>
                      <td>{item.trade_side}</td>
                      <td>{formatAmount(item.executed_premium_value)}</td>
                      <td>{formatAmount(item.slippage_p, 4)}</td>
                      <td className="mono-cell mono-cell--wrap">{item.trade_uuid}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5">No trade history found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </section>
      ) : null}

      {showTriggerModal ? (
        <div className="modal-backdrop" onClick={() => setShowTriggerModal(false)} role="presentation">
          <div className="modal-card" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
            <div className="section-heading">
              <div>
                <p className="eyebrow">{editingTrade ? "Update Trigger" : "Create Trigger"}</p>
                <h2>{editingTrade ? editingTrade.base_asset : "새 트리거"}</h2>
              </div>
            </div>
            <form className="auth-form" onSubmit={handleTriggerSubmit}>
              <label className="auth-form__field" htmlFor="trigger-asset">
                Base Asset
              </label>
              <select
                className="select-input"
                disabled={Boolean(editingTrade)}
                id="trigger-asset"
                onChange={(event) => setTriggerForm((current) => ({ ...current, base_asset: event.target.value }))}
                required
                value={triggerForm.base_asset}
              >
                <option value="">Select asset</option>
                {assets.map((asset) => (
                  <option key={asset.symbol} value={asset.symbol}>
                    {asset.symbol}
                  </option>
                ))}
              </select>
              <label className="auth-form__field" htmlFor="trigger-low">
                Entry
              </label>
              <input
                className="auth-form__input"
                id="trigger-low"
                onChange={(event) => setTriggerForm((current) => ({ ...current, low: event.target.value }))}
                required
                type="number"
                value={triggerForm.low}
              />
              <label className="auth-form__field" htmlFor="trigger-high">
                Exit
              </label>
              <input
                className="auth-form__input"
                id="trigger-high"
                onChange={(event) => setTriggerForm((current) => ({ ...current, high: event.target.value }))}
                required
                type="number"
                value={triggerForm.high}
              />
              <label className="auth-form__field" htmlFor="trigger-capital">
                Trade Capital
              </label>
              <input
                className="auth-form__input"
                id="trigger-capital"
                min="10"
                onChange={(event) => setTriggerForm((current) => ({ ...current, trade_capital: event.target.value }))}
                required
                type="number"
                value={triggerForm.trade_capital}
              />
              <label className="checkbox-row">
                <input
                  checked={triggerForm.usdt_conversion}
                  onChange={(event) =>
                    setTriggerForm((current) => ({
                      ...current,
                      usdt_conversion: event.target.checked,
                    }))
                  }
                  type="checkbox"
                />
                <span>Use USDT conversion</span>
              </label>
              <div className="modal-card__actions">
                <button
                  className="ghost-button ghost-button--button"
                  onClick={() => setShowTriggerModal(false)}
                  type="button"
                >
                  Cancel
                </button>
                <button className="primary-button ghost-button--button" disabled={isBusy} type="submit">
                  {isBusy ? "Saving..." : editingTrade ? "Update" : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {showRepeatModal ? (
        <div className="modal-backdrop" onClick={() => setShowRepeatModal(false)} role="presentation">
          <div className="modal-card" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Auto Repeat</p>
                <h2>{repeatTrade?.base_asset}</h2>
              </div>
            </div>
            <form className="auth-form" onSubmit={handleRepeatSubmit}>
              <label className="checkbox-row">
                <input
                  checked={repeatForm.is_fixed}
                  onChange={(event) =>
                    setRepeatForm((current) => ({
                      ...current,
                      is_fixed: event.target.checked,
                    }))
                  }
                  type="checkbox"
                />
                <span>Fixed mode</span>
              </label>
              {!repeatForm.is_fixed ? (
                <>
                  <label className="auth-form__field" htmlFor="repeat-kline-num">
                    Training Kline
                  </label>
                  <input
                    className="auth-form__input"
                    id="repeat-kline-num"
                    min="50"
                    onChange={(event) =>
                      setRepeatForm((current) => ({
                        ...current,
                        kline_num: event.target.value,
                      }))
                    }
                    type="number"
                    value={repeatForm.kline_num}
                  />
                  <label className="auth-form__field" htmlFor="repeat-pauto-num">
                    Pauto Number
                  </label>
                  <input
                    className="auth-form__input"
                    id="repeat-pauto-num"
                    onChange={(event) =>
                      setRepeatForm((current) => ({
                        ...current,
                        pauto_num: event.target.value,
                      }))
                    }
                    step="0.1"
                    type="number"
                    value={repeatForm.pauto_num}
                  />
                </>
              ) : null}
              <label className="auth-form__field" htmlFor="repeat-auto-num">
                Auto Repeat Count
              </label>
              <input
                className="auth-form__input"
                id="repeat-auto-num"
                min="0"
                onChange={(event) =>
                  setRepeatForm((current) => ({
                    ...current,
                    auto_repeat_num: event.target.value,
                  }))
                }
                type="number"
                value={repeatForm.auto_repeat_num}
              />
              <div className="modal-card__actions">
                <button
                  className="ghost-button ghost-button--button"
                  onClick={() => setShowRepeatModal(false)}
                  type="button"
                >
                  Cancel
                </button>
                <button
                  className="ghost-button ghost-button--button"
                  disabled={isBusy}
                  onClick={handleRepeatDisable}
                  type="button"
                >
                  Disable
                </button>
                <button className="primary-button ghost-button--button" disabled={isBusy} type="submit">
                  {isBusy ? "Saving..." : "Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      ) : null}

      {pageError ? <p className="auth-card__error">{pageError}</p> : null}
    </div>
  );
}
