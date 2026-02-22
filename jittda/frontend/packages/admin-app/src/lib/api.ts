/**
 * API Layer — BaseAPI 클래스 + 레거시 호환 apiFetch.
 */

export const API_BASE: string =
  import.meta.env.VITE_API_BASE || '';

export const WS_BASE: string =
  import.meta.env.VITE_WS_BASE ||
  (API_BASE ? API_BASE.replace(/^http/, 'ws') : '');

export function getWsUrl(path: string): string {
  if (WS_BASE) return `${WS_BASE}${path}`;
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}${path}`;
}

const TOKEN_KEY = 'jittda_token';

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem(TOKEN_KEY);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** @deprecated Use BaseAPI instead */
export function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  return fetch(`${API_BASE}${path}`, { ...init, headers });
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let data: unknown;
    try {
      data = await response.json();
    } catch {
      // non-JSON error body
    }
    const message = typeof data === 'object' && data && 'detail' in data
      ? String((data as { detail: string }).detail)
      : `API Error: ${response.status}`;
    throw new ApiError(response.status, message, data);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export class BaseAPI {
  protected static async get<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: { ...getAuthHeaders() },
    });
    return handleResponse<T>(res);
  }

  protected static async post<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  }

  protected static async put<T>(path: string, body?: unknown): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: body ? JSON.stringify(body) : undefined,
    });
    return handleResponse<T>(res);
  }

  protected static async delete(path: string): Promise<void> {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'DELETE',
      headers: { ...getAuthHeaders() },
    });
    return handleResponse<void>(res);
  }

  protected static async upload<T>(path: string, file: File): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { ...getAuthHeaders() },
      body: formData,
    });
    return handleResponse<T>(res);
  }
}
