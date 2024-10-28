/**
 * Module used to fetch token from Euprhosyne backend and use it to authenticate
 * to external services (like euphrosyne-tools-api).
 */

import { getCSRFToken } from "../../lab/assets/js/utils.js";

export async function jwtFetch(input, init = {}) {
  // Same as fetch, but tries to refresh token if status is 401
  let attemps = 0,
    response;
  while (attemps <= 1) {
    if (attemps > 0) {
      console.info(
        "Received an unauthorized status code. Trying to refresh auth token.",
      );
    }
    const shouldRefreshToken = attemps > 0;
    const token = await getToken(!shouldRefreshToken);
    response = await fetch(input, {
      headers: new Headers({
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      }),
      ...init,
    });
    if (response.status !== 401) {
      return response;
    }
    attemps += 1;
  }
  return response;
}

export async function getToken(checkLocalStorage = true) {
  if (checkLocalStorage) {
    const localToken = localStorage.getItem("euphrosyne-jwt-access");
    if (localToken) return localToken;
  }

  // Try refresh
  const tokenRefresh = getRefreshToken();
  if (tokenRefresh) {
    const access = await refreshToken();
    if (access) {
      saveToken(access, tokenRefresh);
      return access;
    }
  }

  // Fetch new token
  const { access, refresh } = await fetchToken();
  if (access) {
    saveToken(access, refresh);
  }

  if (!access) {
    throw new Error("Failed to get token");
  }
  return access;
}

export function getAccessToken() {
  return localStorage.getItem("euphrosyne-jwt-access");
}

function getRefreshToken() {
  return localStorage.getItem("euphrosyne-jwt-refresh");
}

async function fetchToken() {
  const response = await fetch("/api/auth/token/", {
    method: "POST",
    headers: new Headers({
      "X-CSRFToken": getCSRFToken(),
    }),
  });
  if (response.ok) {
    const { access, refresh } = await response.json();
    return { access, refresh };
  }
  return null;
}

async function refreshToken() {
  const response = await fetch("/api/auth/token/refresh/", {
    method: "POST",
    body: JSON.stringify({
      refresh: localStorage.getItem("euphrosyne-jwt-refresh"),
    }),
    headers: new Headers({
      "X-CSRFToken": getCSRFToken(),
      "Content-Type": "application/json",
    }),
  });
  if (response.ok) {
    const { access } = await response.json();
    return access;
  }
  return null;
}

function saveToken(accessToken, refreshToken = null) {
  localStorage.setItem("euphrosyne-jwt-access", accessToken);
  if (refreshToken) {
    localStorage.setItem("euphrosyne-jwt-refresh", refreshToken);
  }
}
