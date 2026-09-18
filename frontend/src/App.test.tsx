import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import App from "./App";
import { AuthProvider } from "./context/AuthContext";

function renderRoute(route: string) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </MemoryRouter>,
  );
}

describe("Veya authentication UI", () => {
  it("renders the login screen", async () => {
    renderRoute("/login");

    expect(
      await screen.findByRole("heading", { name: /sign in/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /forgot password/i })).toBeInTheDocument();
  });

  it("renders the signup screen", async () => {
    renderRoute("/signup");

    expect(
      await screen.findByRole("heading", { name: /create your account/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm password")).toBeInTheDocument();
  });

  it("validates mismatched signup passwords before calling the API", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const user = userEvent.setup();
    renderRoute("/signup");

    await user.type(screen.getByLabelText("Email"), "creator@example.com");
    await user.type(screen.getByLabelText("Password"), "password-123");
    await user.type(screen.getByLabelText("Confirm password"), "password-456");
    await user.click(screen.getByRole("button", { name: /create account/i }));

    expect(screen.getByText("Passwords do not match.")).toBeInTheDocument();
    expect(fetchSpy).not.toHaveBeenCalled();

    fetchSpy.mockRestore();
  });

  it("submits forgot password and shows the privacy-safe confirmation", async () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          message:
            "If an active Veya account exists for that email, a password reset link has been sent.",
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      ),
    );
    const user = userEvent.setup();
    renderRoute("/forgot-password");

    await user.type(screen.getByLabelText("Email"), "creator@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(
      await screen.findByText(/if an active veya account exists/i),
    ).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalled();

    fetchSpy.mockRestore();
  });

  it("renders and validates the reset password screen", async () => {
    const user = userEvent.setup();
    renderRoute("/reset-password?token=fake-reset-token-value-1234567890");

    expect(
      await screen.findByRole("heading", { name: /choose a new password/i }),
    ).toBeInTheDocument();

    await user.type(screen.getByLabelText("New password"), "password-123");
    await user.type(
      screen.getByLabelText("Confirm new password"),
      "password-456",
    );
    await user.click(screen.getByRole("button", { name: /reset password/i }));

    expect(screen.getByText("Passwords do not match.")).toBeInTheDocument();
  });
});
