import { apiRequest } from "../lib/api";
import type { AuthResponse, AuthUser, TokenResponse } from "../types/auth";

export const authService = {
  signup(email: string, password: string): Promise<AuthResponse> {
    return apiRequest<AuthResponse>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  login(email: string, password: string): Promise<AuthResponse> {
    return apiRequest<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  refresh(refreshToken: string): Promise<TokenResponse> {
    return apiRequest<TokenResponse>("/api/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },

  logout(refreshToken: string): Promise<{ message: string }> {
    return apiRequest<{ message: string }>("/api/auth/logout", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  },

  me(): Promise<AuthUser> {
    return apiRequest<AuthUser>("/api/auth/me");
  },
};
