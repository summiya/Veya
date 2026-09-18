import { apiRequest } from "../lib/api";
import type {
  AudienceHealthSnapshot,
  AudienceTrend,
} from "../types/analytics";

export const analyticsService = {
  captureSnapshot(accountId: number): Promise<AudienceHealthSnapshot> {
    return apiRequest<AudienceHealthSnapshot>(
      `/api/analytics/instagram/accounts/${accountId}/snapshots`,
      { method: "POST" },
    );
  },

  getTrend(accountId: number, days = 30): Promise<AudienceTrend> {
    return apiRequest<AudienceTrend>(
      `/api/analytics/instagram/accounts/${accountId}/trends?days=${days}`,
    );
  },
};
