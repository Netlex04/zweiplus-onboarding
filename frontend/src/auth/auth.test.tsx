import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";
import { getAuthToken } from "../api";

const loginMock = vi.fn();
vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return { ...actual, login: (...args: unknown[]) => loginMock(...args) };
});

afterEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
});

function LoginProbe() {
  const { login, user } = useAuth();
  return (
    <div>
      <button type="button" onClick={() => void login("kunde@demo.test", "demo1234")}>
        do-login
      </button>
      <span>user:{user?.name ?? "none"}</span>
    </div>
  );
}

describe("AuthContext", () => {
  it("stores token + user in state, localStorage and the http layer on login", async () => {
    loginMock.mockResolvedValue({ token: "tok-abc", role: "customer", name: "Demo Kunde" });
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginProbe />
        </AuthProvider>
      </MemoryRouter>,
    );

    await userEvent.click(screen.getByText("do-login"));

    await waitFor(() => expect(screen.getByText("user:Demo Kunde")).toBeInTheDocument());
    expect(getAuthToken()).toBe("tok-abc");
    expect(localStorage.getItem("zweiplus.auth")).toContain("tok-abc");
  });
});

describe("ProtectedRoute", () => {
  it("redirects unauthenticated users to /login", () => {
    render(
      <MemoryRouter initialEntries={["/secret"]}>
        <AuthProvider>
          <Routes>
            <Route
              path="/secret"
              element={
                <ProtectedRoute>
                  <div>secret-content</div>
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div>login-screen</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );
    expect(screen.getByText("login-screen")).toBeInTheDocument();
    expect(screen.queryByText("secret-content")).not.toBeInTheDocument();
  });

  it("allows an authenticated user through", () => {
    localStorage.setItem(
      "zweiplus.auth",
      JSON.stringify({ token: "t", role: "customer", name: "Demo Kunde" }),
    );
    render(
      <MemoryRouter initialEntries={["/secret"]}>
        <AuthProvider>
          <Routes>
            <Route
              path="/secret"
              element={
                <ProtectedRoute>
                  <div>secret-content</div>
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div>login-screen</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>,
    );
    expect(screen.getByText("secret-content")).toBeInTheDocument();
  });
});
