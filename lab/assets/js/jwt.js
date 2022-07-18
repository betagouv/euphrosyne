/**
 * Module used to fetch token from Euprhosyne backend and use it to authenticate
 * to external services (like euphrosyne-tools-api).
 */

import { getCSRFToken } from "./utils.js";

export async function jwtFetch(input, init = {}) {
  // Same as fetch, but tries to refresh token if status is 401
  let attemps = 0,
    response;
  while (attemps <= 1) {
    if (attemps > 0) {
      console.info(
        "Received an unauthorized status code. Trying to refresh auth token."
      );
    }
    const shouldRefreshToken = attemps > 0;
    const token = await getToken(!shouldRefreshToken);
    response = await fetch(input, {
      headers: new Headers({
        Authorization: `Bearer ${token}`,
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
  const token = await fetchToken();
  if (token) {
    localStorage.setItem("euphrosyne-jwt-access", token);
  }
  return token;
}

async function fetchToken() {
  const response = await fetch("/api/auth/token/", {
    method: "POST",
    headers: new Headers({
      "X-CSRFToken": getCSRFToken(),
    }),
  });
  if (response.ok) {
    const { access } = await response.json();
    return access;
  }
  return null;
}
