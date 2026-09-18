import { apiRequest } from "../lib/api";
import type {
  InstagramAccount,
  InstagramMedia,
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
