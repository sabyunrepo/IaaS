/**
 * Shared API configuration.
 *
 * Environment variables follow the VITE_ prefix convention so that
 * Vite exposes them at build time via `import.meta.env`.
 */

export const API_BASE: string =
  import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export const WS_BASE: string =
  import.meta.env.VITE_WS_BASE || 'ws://localhost:8000';
