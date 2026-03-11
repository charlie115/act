"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuth } from "../auth/AuthProvider";

export default function AffiliateRequestClient() {
  const router = useRouter();
  const { authorizedRequest, clearError, error, isLoading, loggedIn, updateUser, user } = useAuth();
  const [form, setForm] = useState({
    contact: "",
    url: "",
    description: "",
    noUrl: false,
    parent_affiliate_code: "",
  });
  const [pageError, setPageError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    clearError();
  }, [clearError]);

  useEffect(() => {
    if (loggedIn && user?.affiliate) {
      router.replace("/affiliate");
    }
  }, [loggedIn, router, user]);

  function setField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setPageError("");
    setIsSubmitting(true);

    try {
      const payload = {
        contact: form.contact,
        url: form.noUrl ? null : form.url,
        description: form.description,
        parent_affiliate_code: form.parent_affiliate_code || null,
      };

      await authorizedRequest("/referral/affiliate-request/", {
        method: "POST",
        body: payload,
      });

      setIsSubmitted(true);
      updateUser({ affiliate_request_pending: true });
    } catch (requestError) {
      const responseError = requestError.payload?.error;

      if (responseError === "REQUEST_EXISTS") {
        setPageError("You have already submitted an application. Please wait for review.");
      } else if (responseError === "INVALID_PARENT_CODE") {
        setPageError("Invalid parent affiliate code. Please check and try again.");
      } else {
        setPageError(requestError.payload?.message || "Failed to submit application.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="surface-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Affiliate</p>
          <h1>제휴 프로그램 신청</h1>
        </div>
      </div>
      {isSubmitted ? (
        <div className="inline-note">
          신청이 접수되었습니다. 검토가 끝날 때까지 기다려 주세요.
        </div>
      ) : (
        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-form__field" htmlFor="contact">
            Contact
          </label>
          <input
            className="auth-form__input"
            id="contact"
            onChange={(event) => setField("contact", event.target.value)}
            placeholder="@telegram_username"
            required
            value={form.contact}
          />

          <label className="auth-form__field" htmlFor="url">
            URL
          </label>
          <input
            className="auth-form__input"
            disabled={form.noUrl}
            id="url"
            onChange={(event) => setField("url", event.target.value)}
            placeholder="https://example.com"
            required={!form.noUrl}
            value={form.url}
          />

          <label className="checkbox-row">
            <input
              checked={form.noUrl}
              onChange={(event) => setField("noUrl", event.target.checked)}
              type="checkbox"
            />
            <span>No URL</span>
          </label>

          <label className="auth-form__field" htmlFor="parent_affiliate_code">
            Parent Affiliate Code
          </label>
          <input
            className="auth-form__input"
            id="parent_affiliate_code"
            onChange={(event) => setField("parent_affiliate_code", event.target.value)}
            placeholder="Optional"
            value={form.parent_affiliate_code}
          />

          <label className="auth-form__field" htmlFor="description">
            Description
          </label>
          <textarea
            className="auth-form__textarea"
            id="description"
            onChange={(event) => setField("description", event.target.value)}
            placeholder="Tell us about your channel, audience, or business."
            required
            rows={6}
            value={form.description}
          />

          <button
            className="primary-button auth-button"
            disabled={!form.contact || (!form.noUrl && !form.url) || !form.description || isSubmitting || isLoading}
            type="submit"
          >
            {isSubmitting ? "Submitting..." : "Submit"}
          </button>
        </form>
      )}
      {pageError || error ? <p className="auth-card__error">{pageError || error}</p> : null}
    </section>
  );
}
