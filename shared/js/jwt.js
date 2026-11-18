/**
 * Module used to fetch token from Euprhosyne backend and use it to authenticate
 * to external services (like euphrosyne-tools-api).
 *
 * The access token is obtained from the web session and kept in memory only:
 * no refresh token and no browser storage, so a token never outlives the
 * session (logout, next user of a shared browser).
 */

import { getCSRFToken } from "../../lab/assets/js/utils.js";
import { jwtDecode } from "jwt-decode";

// Keys used by previous versions to store tokens in localStorage.
const LEGACY_STORAGE_KEYS = ["euphrosyne-jwt-access", "euphrosyne-jwt-refresh"];

let accessToken = null;

function removeLegacyTokens() {
  try {
    LEGACY_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key));
  } catch (e) {
    console.error("Failed to remove legacy tokens", e);
  }
}

removeLegacyTokens();

export async function jwtFetch(input, init = {}, contentType) {
  // Same as fetch, but retries once with a new token if the token is refused
  // (expired or invalid)
  let attempts = 0,
    response;
  while (attempts <= 1) {
    if (attempts > 0) {
      console.info("Received a token refusal. Trying with a new auth token.");
    }
    const token = await getToken(attempts === 0);
    const headers = new Headers({
      ...init.headers,
      Authorization: `Bearer ${token}`,
    });
    if (contentType !== null) {
      // Let the possibility to not set the content type (for form data)
      headers.set("Content-Type", contentType || "application/json");
    }
    if (init.method !== "GET") {
      headers.set("X-CSRFToken", getCSRFToken());
    }
    response = await fetch(input, {
      headers,
      ...init,
    });
    if (response.status !== 401) {
      return response;
    }
    attempts += 1;
  }
  return response;
}

function isValid(token) {
  try {
    return jwtDecode(token).exp > Date.now() / 1000;
  } catch (e) {
    console.error("Failed to decode token", e);
    return false;
  }
}

export async function getToken(checkCache = true) {
  if (checkCache && accessToken && isValid(accessToken)) {
    return accessToken;
  }
  accessToken = await fetchToken();
  return accessToken;
}

async function fetchToken() {
  const response = await fetch("/api/auth/token/", {
    method: "POST",
    headers: new Headers({
      "X-CSRFToken": getCSRFToken(),
    }),
  });
  let data = null;
  try {
    data = await response.json();
  } catch {
    // Not a JSON response
  }
  if (response.ok && data?.access) {
    return data.access;
  }
  if (!response.ok && data?.redirect_url) {
    // The session must complete a step first (second factor, CGU...).
    window.location.assign(data.redirect_url);
    throw new Error(
      `Failed to get token: ${data.detail || data.code || response.status}`,
    );
  }
  throw new Error(`Failed to get token (status ${response.status})`);
}
