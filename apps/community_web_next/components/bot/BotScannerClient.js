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

export default function BotScannerClient({ selectedConfig }) {
  const { authorizedListRequest, authorizedRequest } = useAuth();
  const [scannerData, setScannerData] = useState([]);
  const [pageError, setPageError] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    low: "",
    high: "",
    trade_capital: "100",
    min_target_atp: "",
    min_origin_funding_rate: "",
    max_repeat_num: "",
    repeat_term_secs: "300",
  });

  useEffect(() => {
    let active = true;

    async function loadPage() {
      setPageError("");

      try {
        const nextScannerData = await authorizedListRequest(
          `/tradecore/trigger-scanner/?trade_config_uuid=${selectedConfig.trade_config_uuid}`
        );

        if (!active) {
          return;
        }

        setScannerData(nextScannerData);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load trigger scanners.");
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [authorizedListRequest, selectedConfig.trade_config_uuid]);

  async function reloadScanner() {
    const nextScannerData = await authorizedListRequest(
      `/tradecore/trigger-scanner/?trade_config_uuid=${selectedConfig.trade_config_uuid}`
    );
    setScannerData(nextScannerData);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest("/tradecore/trigger-scanner/", {
        method: "POST",
        body: {
          trade_config_uuid: selectedConfig.trade_config_uuid,
          low: Number(form.low),
          high: Number(form.high),
          trade_capital: Number(form.trade_capital),
          min_target_atp: form.min_target_atp ? Number(form.min_target_atp) : undefined,
          min_origin_funding_rate: form.min_origin_funding_rate
            ? Number(form.min_origin_funding_rate)
            : undefined,
          max_repeat_num: form.max_repeat_num ? Number(form.max_repeat_num) : undefined,
          repeat_term_secs: form.repeat_term_secs ? Number(form.repeat_term_secs) : undefined,
        },
      });

      setShowForm(false);
      setForm({
        low: "",
        high: "",
        trade_capital: "100",
        min_target_atp: "",
        min_origin_funding_rate: "",
        max_repeat_num: "",
        repeat_term_secs: "300",
      });
      await reloadScanner();
    } catch (requestError) {
      setPageError(requestError.payload?.detail || requestError.message || "Failed to create scanner.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDelete(item) {
    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest(
        `/tradecore/trigger-scanner/${item.uuid}/?trade_config_uuid=${selectedConfig.trade_config_uuid}`,
        { method: "DELETE" }
      );
      await reloadScanner();
    } catch (requestError) {
      setPageError(requestError.message || "Failed to delete scanner.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Scanner</p>
            <h1>Trigger Scanner 관리</h1>
          </div>
          <button className="primary-button ghost-button--button" onClick={() => setShowForm(true)} type="button">
            Add Scanner
          </button>
        </div>
        <div className="table-shell">
          <table className="data-table">
            <thead>
              <tr>
                <th>Entry</th>
                <th>Exit</th>
                <th>Trade Capital</th>
                <th>Min Target ATP</th>
                <th>Min Origin Funding</th>
                <th>Max Repeat</th>
                <th>Repeat Term</th>
                <th>Delete</th>
              </tr>
            </thead>
            <tbody>
              {scannerData.length ? (
                scannerData.map((item) => (
                  <tr key={item.uuid}>
                    <td>{formatAmount(item.low)}</td>
                    <td>{formatAmount(item.high)}</td>
                    <td>{formatAmount(item.trade_capital, 0)}</td>
                    <td>{formatAmount(item.min_target_atp)}</td>
                    <td>{formatAmount(item.min_origin_funding_rate, 6)}</td>
                    <td>{formatAmount(item.max_repeat_num, 0)}</td>
                    <td>{formatAmount(item.repeat_term_secs, 0)}s</td>
                    <td>
                      <button
                        className="ghost-button ghost-button--button"
                        onClick={() => handleDelete(item)}
                        type="button"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8">No trigger scanners configured.</td>
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
                <p className="eyebrow">Create Scanner</p>
                <h2>새 Trigger Scanner</h2>
              </div>
            </div>
            <form className="auth-form" onSubmit={handleSubmit}>
              <label className="auth-form__field" htmlFor="scanner-low">
                Entry
              </label>
              <input
                className="auth-form__input"
                id="scanner-low"
                onChange={(event) => setForm((current) => ({ ...current, low: event.target.value }))}
                required
                type="number"
                value={form.low}
              />
              <label className="auth-form__field" htmlFor="scanner-high">
                Exit
              </label>
              <input
                className="auth-form__input"
                id="scanner-high"
                onChange={(event) => setForm((current) => ({ ...current, high: event.target.value }))}
                required
                type="number"
                value={form.high}
              />
              <label className="auth-form__field" htmlFor="scanner-capital">
                Trade Capital
              </label>
              <input
                className="auth-form__input"
                id="scanner-capital"
                min="10"
                onChange={(event) => setForm((current) => ({ ...current, trade_capital: event.target.value }))}
                required
                type="number"
                value={form.trade_capital}
              />
              <label className="auth-form__field" htmlFor="scanner-target-atp">
                Minimum Target ATP
              </label>
              <input
                className="auth-form__input"
                id="scanner-target-atp"
                onChange={(event) => setForm((current) => ({ ...current, min_target_atp: event.target.value }))}
                type="number"
                value={form.min_target_atp}
              />
              <label className="auth-form__field" htmlFor="scanner-origin-fr">
                Minimum Origin Funding Rate
              </label>
              <input
                className="auth-form__input"
                id="scanner-origin-fr"
                onChange={(event) => setForm((current) => ({ ...current, min_origin_funding_rate: event.target.value }))}
                type="number"
                value={form.min_origin_funding_rate}
              />
              <label className="auth-form__field" htmlFor="scanner-max-repeat">
                Maximum Iteration
              </label>
              <input
                className="auth-form__input"
                id="scanner-max-repeat"
                onChange={(event) => setForm((current) => ({ ...current, max_repeat_num: event.target.value }))}
                type="number"
                value={form.max_repeat_num}
              />
              <label className="auth-form__field" htmlFor="scanner-repeat-term">
                Iteration Interval (seconds)
              </label>
              <input
                className="auth-form__input"
                id="scanner-repeat-term"
                onChange={(event) => setForm((current) => ({ ...current, repeat_term_secs: event.target.value }))}
                type="number"
                value={form.repeat_term_secs}
              />
              <div className="modal-card__actions">
                <button
                  className="ghost-button ghost-button--button"
                  onClick={() => setShowForm(false)}
                  type="button"
                >
                  Cancel
                </button>
                <button className="primary-button ghost-button--button" disabled={isBusy} type="submit">
                  {isBusy ? "Creating..." : "Create"}
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
