import { getAccessToken } from "@/lib/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api";

function ensurePath(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

export function withQuery(path: string, query: Record<string, string | number | undefined>) {
  const url = new URL(`${API_BASE_URL}${ensurePath(path)}`);
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === "") return;
    url.searchParams.set(key, String(value));
  });
  return url.toString();
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  options: { auth?: boolean } = {},
): Promise<T> {
  const headers = new Headers(init.headers ?? {});
  headers.set("Content-Type", "application/json");

  if (options.auth) {
    const token = getAccessToken();
    if (!token) {
      throw new Error("You need to sign in first.");
    }
    headers.set("Authorization", `Bearer ${token}`);
  }

  const res = await fetch(`${API_BASE_URL}${ensurePath(path)}`, {
    ...init,
    headers,
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = "Request failed";
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (typeof body?.message === "string") detail = body.message;
      else if (body && typeof body === "object") detail = JSON.stringify(body);
    } catch {
      // keep default
    }
    throw new Error(detail);
  }

  if (res.status === 204) {
    return {} as T;
  }
  return (await res.json()) as T;
}

export function apiGet<T>(path: string, options: { auth?: boolean } = {}) {
  return apiRequest<T>(path, { method: "GET" }, options);
}

export function apiPost<T>(path: string, body: unknown, options: { auth?: boolean } = {}) {
  return apiRequest<T>(path, { method: "POST", body: JSON.stringify(body) }, options);
}

export function apiPatch<T>(path: string, body: unknown, options: { auth?: boolean } = {}) {
  return apiRequest<T>(path, { method: "PATCH", body: JSON.stringify(body) }, options);
}
