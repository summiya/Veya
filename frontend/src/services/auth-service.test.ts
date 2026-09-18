import { afterEach, describe, expect, it, vi } from "vitest";

import { authStorage } from "../lib/auth-storage";
import { authService } from "./auth-service";

afterEach(() => {
  vi.restoreAllMocks();
  authStorage.clear();
});

describe("authService", () => {
  it("posts login credentials to the backend", async () => {
    const response = {
      user: {
        uuid: "user-1",
        email: "creator@example.com",
        is_active: true,
        created_at: new Date().toISOString(),
      },
      access_token: "access",
      refresh_token: "refresh",
      token_type: "bearer" as const,
    };

    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(response), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(
      authService.login("creator@example.com", "password-123"),
    ).resolves.toEqual(response);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/login",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "creator@example.com",
          password: "password-123",
        }),
      }),
    );
  });

  it("sends the access token for the me endpoint", async () => {
    authStorage.setTokens("access-token", "refresh-token");

    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          uuid: "user-1",
          email: "creator@example.com",
          is_active: true,
          created_at: new Date().toISOString(),
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );

    await authService.me();

    const request = fetchMock.mock.calls[0];
    const headers = new Headers((request[1] as RequestInit).headers);
    expect(headers.get("Authorization")).toBe("Bearer access-token");
  });
});
