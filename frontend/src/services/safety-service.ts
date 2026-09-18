import { apiRequest } from "../lib/api";
import type {
  SafetyAnalyzeResult,
  SafetyComment,
  SafetySummary,
} from "../types/safety";

export const safetyService = {
  analyzeAccount(accountId: number): Promise<SafetyAnalyzeResult> {
    return apiRequest<SafetyAnalyzeResult>(
      `/api/safety/instagram/accounts/${accountId}/analyze`,
      { method: "POST" },
    );
  },

  getSummary(accountId: number): Promise<SafetySummary> {
    return apiRequest<SafetySummary>(
      `/api/safety/instagram/accounts/${accountId}`,
    );
  },

  getFeed(accountId: number): Promise<SafetyComment[]> {
    return apiRequest<SafetyComment[]>(
      `/api/safety/instagram/accounts/${accountId}/feed`,
    );
  },

  getShielded(accountId: number, reveal = false): Promise<SafetyComment[]> {
    return apiRequest<SafetyComment[]>(
      `/api/safety/instagram/accounts/${accountId}/shielded?reveal=${reveal}`,
    );
  },
};
