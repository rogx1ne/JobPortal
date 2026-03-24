const ACCESS_TOKEN_KEY = "jobportal_access_token";
const REFRESH_TOKEN_KEY = "jobportal_refresh_token";

function canUseStorage() {
  return typeof window !== "undefined";
}

export function getAccessToken() {
  if (!canUseStorage()) return "";
  return window.localStorage.getItem(ACCESS_TOKEN_KEY) ?? "";
}

export function getRefreshToken() {
  if (!canUseStorage()) return "";
  return window.localStorage.getItem(REFRESH_TOKEN_KEY) ?? "";
}

export function setSession(access: string, refresh: string) {
  if (!canUseStorage()) return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, access);
  window.localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

export function clearSession() {
  if (!canUseStorage()) return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function isLoggedIn() {
  return Boolean(getAccessToken());
}
