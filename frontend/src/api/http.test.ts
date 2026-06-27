import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRequest, ApiError, setAuthToken } from "./http";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiRequest error mapping", () => {
  beforeEach(() => {
    setAuthToken(null);
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("maps a backend {error, detail} body onto ApiError", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ error: "unauthorized", detail: "Nicht authentifiziert" }, 401),
    );

    await expect(apiRequest("/api/x")).rejects.toMatchObject({
      status: 401,
      code: "unauthorized",
      detail: "Nicht authentifiziert",
    });
    await expect(apiRequest("/api/x")).rejects.toBeInstanceOf(ApiError);
  });

  it("falls back gracefully on a non-JSON error body", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response("boom", { status: 500, statusText: "Internal Server Error" }),
    );
    await expect(apiRequest("/api/x")).rejects.toMatchObject({ status: 500, code: "error" });
  });

  it("wraps network failures as ApiError(network_error)", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(apiRequest("/api/x")).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
  });

  it("attaches the Bearer token when set", async () => {
    setAuthToken("tok-123");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse({ ok: true }));
    await apiRequest("/api/x");
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer tok-123");
  });
});
