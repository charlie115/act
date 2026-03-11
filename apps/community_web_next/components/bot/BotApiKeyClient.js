"use client";

import { useEffect, useMemo, useState } from "react";

import { useAuth } from "../auth/AuthProvider";

function formatDate(value) {
  if (!value) {
    return "-";
  }

  return new Date(value).toLocaleString();
}

function truncateValue(value, head = 8, tail = 4) {
  if (!value) {
    return "-";
  }

  if (value.length <= head + tail + 3) {
    return value;
  }

  return `${value.slice(0, head)}...${value.slice(-tail)}`;
}

function MarketApiKeyTable({ items, onAdd, onDelete, title }) {
  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">API Key</p>
          <h2>{title}</h2>
        </div>
        <button className="primary-button ghost-button--button" onClick={onAdd} type="button">
          Add
        </button>
      </div>
      <div className="table-shell">
        <table className="data-table">
          <thead>
            <tr>
              <th>Registered</th>
              <th>Access Key</th>
              <th>Secret Key</th>
              <th>Delete</th>
            </tr>
          </thead>
          <tbody>
            {items.length ? (
              items.map((item) => (
                <tr key={item.uuid}>
                  <td>{formatDate(item.registered_datetime)}</td>
                  <td className="mono-cell">{truncateValue(item.access_key)}</td>
                  <td>●●●●●●</td>
                  <td>
                    <button
                      className="ghost-button ghost-button--button"
                      onClick={() => onDelete(item)}
                      type="button"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="4">No API keys registered.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function BotApiKeyClient({ marketCodeCombination, selectedConfig }) {
  const { authorizedListRequest, authorizedRequest } = useAuth();
  const [apiKeys, setApiKeys] = useState([]);
  const [nodeIp, setNodeIp] = useState("");
  const [pageError, setPageError] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [marketCodeForm, setMarketCodeForm] = useState(null);
  const [form, setForm] = useState({
    access_key: "",
    secret_key: "",
    passphrase: "",
  });

  useEffect(() => {
    let active = true;

    async function loadPage() {
      setPageError("");

      try {
        const [nextApiKeys, nodes] = await Promise.all([
          authorizedListRequest(
            `/tradecore/exchange-api-key/?trade_config_uuid=${selectedConfig.trade_config_uuid}`
          ),
          authorizedListRequest("/tradecore/nodes/"),
        ]);

        if (!active) {
          return;
        }

        setApiKeys(nextApiKeys);
        const node = nodes?.results?.find?.((item) => item.id === selectedConfig.node) || nodes.find?.((item) => item.id === selectedConfig.node);
        const nodeUrl = node?.url || "";
        const parsedNodeIp = nodeUrl.includes("://")
          ? nodeUrl.split("://")[1].split(":")[0]
          : "";
        setNodeIp(parsedNodeIp);
      } catch (requestError) {
        if (!active) {
          return;
        }

        setPageError(requestError.message || "Failed to load API keys.");
      }
    }

    loadPage();

    return () => {
      active = false;
    };
  }, [authorizedListRequest, selectedConfig.node, selectedConfig.trade_config_uuid]);

  const targetItems = useMemo(
    () => apiKeys.filter((item) => item.market_code === marketCodeCombination.target.value),
    [apiKeys, marketCodeCombination.target.value]
  );
  const originItems = useMemo(
    () => apiKeys.filter((item) => item.market_code === marketCodeCombination.origin.value),
    [apiKeys, marketCodeCombination.origin.value]
  );

  async function reloadKeys() {
    const nextApiKeys = await authorizedListRequest(
      `/tradecore/exchange-api-key/?trade_config_uuid=${selectedConfig.trade_config_uuid}`
    );
    setApiKeys(nextApiKeys);
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!marketCodeForm) {
      return;
    }

    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest("/tradecore/exchange-api-key/", {
        method: "POST",
        body: {
          trade_config_uuid: selectedConfig.trade_config_uuid,
          market_code: marketCodeForm.value,
          access_key: form.access_key,
          secret_key: form.secret_key,
          passphrase: marketCodeForm.exchange === "OKX" ? form.passphrase : undefined,
        },
      });

      setMarketCodeForm(null);
      setForm({ access_key: "", secret_key: "", passphrase: "" });
      await reloadKeys();
    } catch (requestError) {
      setPageError(
        requestError.payload?.detail ||
          requestError.payload?.code?.[0] ||
          "Failed to register API key."
      );
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDelete(item) {
    setIsBusy(true);
    setPageError("");

    try {
      await authorizedRequest(
        `/tradecore/exchange-api-key/${item.uuid}/?trade_config_uuid=${selectedConfig.trade_config_uuid}`,
        { method: "DELETE" }
      );
      await reloadKeys();
    } catch (requestError) {
      setPageError(requestError.message || "Failed to delete API key.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <div className="section-stack">
      <section className="surface-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Node</p>
            <h1>API Key 등록 안내</h1>
          </div>
        </div>
        <div className="inline-note">
          API 키 발급 시 허용 IP에 <strong>{nodeIp || "allocated node ip"}</strong> 를 포함해야 합니다.
        </div>
      </section>

      <div className="two-column-grid">
        <MarketApiKeyTable
          items={targetItems}
          onAdd={() => setMarketCodeForm(marketCodeCombination.target)}
          onDelete={handleDelete}
          title={marketCodeCombination.target.value}
        />
        <MarketApiKeyTable
          items={originItems}
          onAdd={() => setMarketCodeForm(marketCodeCombination.origin)}
          onDelete={handleDelete}
          title={marketCodeCombination.origin.value}
        />
      </div>

      {marketCodeForm ? (
        <div className="modal-backdrop" onClick={() => setMarketCodeForm(null)} role="presentation">
          <div className="modal-card" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Exchange API Key</p>
                <h2>{marketCodeForm.value}</h2>
              </div>
            </div>
            <form className="auth-form" onSubmit={handleSubmit}>
              <label className="auth-form__field" htmlFor="access-key">
                Access Key
              </label>
              <input
                className="auth-form__input"
                id="access-key"
                onChange={(event) => setForm((current) => ({ ...current, access_key: event.target.value }))}
                required
                value={form.access_key}
              />
              <label className="auth-form__field" htmlFor="secret-key">
                Secret Key
              </label>
              <input
                className="auth-form__input"
                id="secret-key"
                onChange={(event) => setForm((current) => ({ ...current, secret_key: event.target.value }))}
                required
                type="password"
                value={form.secret_key}
              />
              {marketCodeForm.exchange === "OKX" ? (
                <>
                  <label className="auth-form__field" htmlFor="passphrase">
                    Passphrase
                  </label>
                  <input
                    className="auth-form__input"
                    id="passphrase"
                    onChange={(event) => setForm((current) => ({ ...current, passphrase: event.target.value }))}
                    required
                    type="password"
                    value={form.passphrase}
                  />
                </>
              ) : null}
              <div className="modal-card__actions">
                <button
                  className="ghost-button ghost-button--button"
                  onClick={() => setMarketCodeForm(null)}
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
