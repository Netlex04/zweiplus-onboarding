/**
 * Low-level HTTP layer: base URL, Bearer token injection and centralized
 * error mapping of the backend `{ error, detail }` schema into ApiError.
 */

import type { ApiErrorBody } from "./types";

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") ??
  "http://localhost:8000";

/** Error carrying the backend `{ error, detail }` payload plus HTTP status. */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly detail: string;

  constructor(status: number, code: string, detail: string) {
    super(detail || code || `HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

// In-memory token; AuthContext keeps it in sync with localStorage.
let authToken: string | null = null;

export function setAuthToken(token: string | null): void {
  authToken = token;
}

export function getAuthToken(): string | null {
  return authToken;
}

interface RequestOptions {
  method?: string;
  /** JSON body; omitted for GET. Ignored when `formData` is provided. */
  body?: unknown;
  /** Multipart body for file uploads. */
  formData?: FormData;
  /** Extra query params (string values). */
  query?: Record<string, string | undefined>;
  signal?: AbortSignal;
}

function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(API_BASE_URL + path);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined) url.searchParams.set(key, value);
    }
  }
  return url.toString();
}

async function toApiError(response: Response): Promise<ApiError> {
  let code = "error";
  let detail = response.statusText;
  try {
    const data = (await response.json()) as Partial<ApiErrorBody>;
    if (data && typeof data === "object") {
      if (typeof data.error === "string") code = data.error;
      if (typeof data.detail === "string") detail = data.detail;
    }
  } catch {
    // Non-JSON error body — keep status text.
  }
  return new ApiError(response.status, code, detail);
}

/** Perform a request and parse a JSON response into `T`. */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, formData, query, signal } = options;

  const headers: Record<string, string> = {};
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  let payload: BodyInit | undefined;
  if (formData) {
    payload = formData; // browser sets multipart Content-Type + boundary
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), { method, headers, body: payload, signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(0, "network_error", "Verbindung zum Server fehlgeschlagen.");
  }

  if (!response.ok) throw await toApiError(response);

  if (response.status === 204) return undefined as T;
  const text = await response.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

/** Build an authenticated URL (e.g. for downloads opened in a new tab). */
export function buildAuthedUrl(path: string, query?: Record<string, string | undefined>): string {
  return buildUrl(path, query);
}

/**
 * Fetch a binary resource with the Bearer token attached and return the blob
 * plus any filename advertised via Content-Disposition. Used for protected
 * file downloads (uploads, template files) that cannot use a bare anchor.
 */
export async function fetchBlob(
  path: string,
  query?: RequestOptions["query"],
): Promise<{ blob: Blob; fileName: string | null }> {
  const headers: Record<string, string> = {};
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  let response: Response;
  try {
    response = await fetch(buildUrl(path, query), { headers });
  } catch {
    throw new ApiError(0, "network_error", "Verbindung zum Server fehlgeschlagen.");
  }
  if (!response.ok) throw await toApiError(response);

  const disposition = response.headers.get("Content-Disposition");
  const match = disposition?.match(/filename="?([^"]+)"?/i);
  return { blob: await response.blob(), fileName: match ? match[1] : null };
}
