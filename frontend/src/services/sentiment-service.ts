import { apiRequest } from "../lib/api";
import type {
  AnalyzeSentimentResult,
  SentimentSummary,
} from "../types/sentiment";

export const sentimentService = {
  analyzeAccount(accountId: number): Promise<AnalyzeSentimentResult> {
    return apiRequest<AnalyzeSentimentResult>(
      `/api/sentiment/instagram/accounts/${accountId}/analyze`,
      { method: "POST" },
    );
  },

  getAccountSummary(accountId: number): Promise<SentimentSummary> {
    return apiRequest<SentimentSummary>(
      `/api/sentiment/instagram/accounts/${accountId}`,
    );
  },

  getMediaSummary(accountId: number, mediaId: number): Promise<SentimentSummary> {
    return apiRequest<SentimentSummary>(
      `/api/sentiment/instagram/accounts/${accountId}/media/${mediaId}`,
    );
  },
};
