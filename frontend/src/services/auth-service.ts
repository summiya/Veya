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

  forgotPassword(email: string): Promise<{ message: string }> {
    return apiRequest<{ message: string }>("/api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },

  resetPassword(token: string, password: string): Promise<{ message: string }> {
    return apiRequest<{ message: string }>("/api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, password }),
    });
  },

  me(): Promise<AuthUser> {
    return apiRequest<AuthUser>("/api/auth/me");
  },
};
