import { apiRequest } from "../lib/api";
import type {
  InstagramAccount,
  InstagramConnectionCheck,
  InstagramMedia,
  InstagramReadiness,
  InstagramSyncResult,
} from "../types/instagram";

export const instagramService = {
  listAccounts(): Promise<InstagramAccount[]> {
    return apiRequest<InstagramAccount[]>("/api/integrations/instagram/accounts");
  },

  connect(): Promise<{ authorization_url: string }> {
    return apiRequest<{ authorization_url: string }>(
      "/api/integrations/instagram/connect",
    );
  },

  readiness(): Promise<InstagramReadiness> {
    return apiRequest<InstagramReadiness>("/api/integrations/instagram/readiness");
  },

  checkConnection(accountId: number): Promise<InstagramConnectionCheck> {
    return apiRequest<InstagramConnectionCheck>(
      `/api/integrations/instagram/accounts/${accountId}/check`,
      { method: "POST" },
    );
  },

  refreshToken(accountId: number): Promise<InstagramConnectionCheck> {
    return apiRequest<InstagramConnectionCheck>(
      `/api/integrations/instagram/accounts/${accountId}/refresh-token`,
      { method: "POST" },
    );
  },

  disconnect(accountId: number): Promise<{ message: string }> {
    return apiRequest<{ message: string }>(
      `/api/integrations/instagram/accounts/${accountId}`,
      { method: "DELETE" },
    );
  },

  sync(accountId: number): Promise<InstagramSyncResult> {
    return apiRequest<InstagramSyncResult>(
      `/api/integrations/instagram/accounts/${accountId}/sync`,
      { method: "POST" },
    );
  },

  listMedia(accountId: number): Promise<InstagramMedia[]> {
    return apiRequest<InstagramMedia[]>(
      `/api/integrations/instagram/accounts/${accountId}/media`,
    );
  },
};
