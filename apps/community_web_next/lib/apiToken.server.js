/**
 * Server-only module for generating HMAC-signed API tokens.
 * These tokens are validated by Django's ApiTokenMiddleware.
 *
 * Token format: `{timestamp_hex}.{hmac_signature}`
 * TTL: 5 minutes
 */

import { createHmac } from "crypto";

const SECRET = process.env.API_TOKEN_SECRET || "dev-api-token-secret-change-in-production";
const TTL_MS = 5 * 60 * 1000; // 5 minutes

export function generateApiToken() {
  const timestamp = Date.now();
  const payload = String(timestamp);
  const signature = createHmac("sha256", SECRET).update(payload).digest("hex");
  return `${timestamp.toString(16)}.${signature}`;
}

export function getTokenExpiry() {
  return TTL_MS;
}
