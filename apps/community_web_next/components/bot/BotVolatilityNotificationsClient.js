"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthProvider";

export default function BotVolatilityNotificationsClient() {
  const { authorizedListRequest, authorizedRequest } = useAuth();
  const [configs, setConfigs] = useState([]);
  const [marketCodes, setMarketCodes] = useState({});
  const [pageError, setPageError] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [form, setForm] = useState({
    market_code_combination: "",
    volatility_threshold: "0.5",
    notification_interval_minutes: "180",
    enabled: true,
  });

  useEffect(() => {
    let active = true;

    async function loadPage() {
      setPageError("");

      try {
        const [nextConfigs, nextMarketCodes] = await Promise.all([
          authorizedListRequest("/infocore/volatility-notifications/"),
          fetch("/api/infocore/market-codes/", { cache: "no-store" }).then((response) => response.json()),
        ]);

        if (!active) {
          return;
        }

        setConfigs(nextConfigs);
        setMarketCodes(nextMarketCodes || {});
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load volatility notifications.");
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [authorizedListRequest]);

  const combinations = useMemo(() => {
    const items = [];

    Object.entries(marketCodes || {}).forEach(([target, origins]) => {
      origins.forEach((origin) => {
        items.push({
          label: `${target} : ${origin}`,
          value: `${target}:${origin}`,
        });
      });
    });

    return items;
  }, [marketCodes]);

  async function reloadConfigs() {
    const nextConfigs = await authorizedListRequest("/infocore/volatility-notifications/");
    setConfigs(nextConfigs);
  }

  function openForm(config = null) {
    if (config) {
      setEditingConfig(config);
      setForm({
        market_code_combination: `${config.target_market_code}:${config.origin_market_code}`,
        volatility_threshold: String(config.volatility_threshold),
        notification_interval_minutes: String(config.notification_interval_minutes),
        enabled: Boolean(config.enabled),
      });
    } else {
      setEditingConfig(null);
      setForm({
        market_code_combination: "",
        volatility_threshold: "0.5",
        notification_interval_minutes: "180",
        enabled: true,
      });
    }
    setShowForm(true);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsBusy(true);
    setPageError("");

    try {
      const [target_market_code, origin_market_code] = form.market_code_combination.split(":");
      const payload = {
        target_market_code,
        origin_market_code,
        volatility_threshold: Number(form.volatility_threshold),
        notification_interval_minutes: Number(form.notification_interval_minutes),
        enabled: Boolean(form.enabled),
      };

      if (editingConfig) {
        await authorizedRequest(`/infocore/volatility-notifications/${editingConfig.id}/`, {
          method: "PATCH",
          body: payload,
        });
      } else {
        await authorizedRequest("/infocore/volatility-notifications/", {
          method: "POST",
          body: payload,
        });
      }

      setShowForm(false);
      setEditingConfig(null);
      await reloadConfigs();
    } catch (requestError) {
      setPageError(requestError.payload?.detail || requestError.message || "Failed to save configuration.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDelete(id) {
    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest(`/infocore/volatility-notifications/${id}/`, {
        method: "DELETE",
      });
      await reloadConfigs();
    } catch (requestError) {
      setPageError(requestError.message || "Failed to delete configuration.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Settings</p>
            <h1>변동성 알림 설정</h1>
          </div>
          <button className="primary-button ghost-button--button" onClick={() => openForm()} type="button">
            Add Configuration
          </button>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Market Codes</th>
                <th>Threshold</th>
                <th>Interval</th>
                <th>Enabled</th>
                <th>Edit</th>
                <th>Delete</th>
              </tr>
            </thead>
            <tbody>
              {configs.length ? (
                configs.map((config) => (
                  <tr key={config.id}>
                    <td>{config.target_market_code} : {config.origin_market_code}</td>
                    <td>{config.volatility_threshold}</td>
                    <td>{config.notification_interval_minutes} min</td>
                    <td>{config.enabled ? "On" : "Off"}</td>
                    <td>
                      <button
                        className="ghost-button ghost-button--button"
                        onClick={() => openForm(config)}
                        type="button"
                      >
                        Edit
                      </button>
                    </td>
                    <td>
                      <button
                        className="ghost-button ghost-button--button"
                        onClick={() => handleDelete(config.id)}
                        type="button"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="6">No volatility notification configs.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {showForm ? (
        <div className="modal-backdrop" onClick={() => setShowForm(false)} role="presentation">
          <div className="modal-card" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Volatility Notification</p>
                <h2>{editingConfig ? "Edit Configuration" : "Add Configuration"}</h2>
              </div>
            </div>
            <form className="auth-form" onSubmit={handleSubmit}>
              <label className="auth-form__field" htmlFor="volatility-market-code">
                Market Codes
              </label>
              <select
                className="select-input"
                id="volatility-market-code"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    market_code_combination: event.target.value,
                  }))
                }
                required
                value={form.market_code_combination}
              >
                <option value="">Select market combination</option>
                {combinations.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>

              <label className="auth-form__field" htmlFor="volatility-threshold">
                Volatility Threshold
              </label>
              <input
                className="auth-form__input"
                id="volatility-threshold"
                min="0"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    volatility_threshold: event.target.value,
                  }))
                }
                required
                step="0.01"
                type="number"
                value={form.volatility_threshold}
              />

              <label className="auth-form__field" htmlFor="volatility-interval">
                Notification Interval (minutes)
              </label>
              <input
                className="auth-form__input"
                id="volatility-interval"
                min="1"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    notification_interval_minutes: event.target.value,
                  }))
                }
                required
                type="number"
                value={form.notification_interval_minutes}
              />

              <label className="checkbox-row">
                <input
                  checked={form.enabled}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      enabled: event.target.checked,
                    }))
                  }
                  type="checkbox"
                />
                <span>Enabled</span>
              </label>

              <div className="modal-card__actions">
                <button
                  className="ghost-button ghost-button--button"
                  onClick={() => setShowForm(false)}
                  type="button"
                >
                  Cancel
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
