export type SentimentSummary = {
  total: number;
  positive: number;
  neutral: number;
  negative: number;
  positive_percentage: number;
  neutral_percentage: number;
  negative_percentage: number;
};

export type AnalyzeSentimentResult = {
  analyzed_comments: number;
};
