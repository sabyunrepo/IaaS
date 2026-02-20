/**
 * Shared API configuration.
 *
 * Environment variables follow the VITE_ prefix convention so that
 * Vite exposes them at build time via `import.meta.env`.
 */

export const API_BASE: string =
  import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export const WS_BASE: string =
  import.meta.env.VITE_WS_BASE ||
  API_BASE.replace(/^http/, 'ws') ||
  'ws://localhost:8000';

const TOKEN_KEY = 'jittda_token';

/** Authenticated fetch wrapper. Injects Authorization header when token exists. */
export function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const token = localStorage.getItem(TOKEN_KEY);
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return fetch(`${API_BASE}${path}`, { ...init, headers });
}
