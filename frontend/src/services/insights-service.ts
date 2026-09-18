import { apiRequest } from "../lib/api";
import type { AudienceInsight } from "../types/insights";

export const insightsService = {
  getCurrent(accountId: number): Promise<AudienceInsight | null> {
    return apiRequest<AudienceInsight | null>(
      `/api/insights/instagram/accounts/${accountId}`,
    );
  },

  generate(accountId: number): Promise<AudienceInsight> {
    return apiRequest<AudienceInsight>(
      `/api/insights/instagram/accounts/${accountId}/generate`,
      { method: "POST" },
    );
  },
};
