import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { authApi } from "../../api/client";
import { LoginPage } from "./LoginPage";

vi.mock("../../api/client", () => ({
  authApi: { google: vi.fn() },
}));

const mockedApi = vi.mocked(authApi);

beforeEach(() => {
  vi.clearAllMocks();
  document.querySelector("#google-identity-services")?.remove();
});

describe("LoginPage", () => {
  it("posts the GIS credential and sends a new user to level onboarding", async () => {
    let credentialCallback: ((response: { credential: string }) => void) | undefined;
    window.google = {
      accounts: {
        id: {
          initialize: vi.fn((options) => {
            credentialCallback = options.callback;
          }),
          renderButton: vi.fn(),
        },
      },
    };
    mockedApi.google.mockResolvedValue({
      id: 7,
      name: "Yuki",
      email: "yuki@example.com",
      picture: null,
      level_band: null,
      onboarded: false,
    });

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage clientId="test-client-id" />} />
          <Route path="/onboarding/level" element={<h1>レベル設定</h1>} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(window.google?.accounts.id.renderButton).toHaveBeenCalled());
    credentialCallback?.({ credential: "google-jwt" });

    expect(mockedApi.google).toHaveBeenCalledWith("google-jwt");
    expect(await screen.findByRole("heading", { name: "レベル設定" })).toBeInTheDocument();
  });
});
