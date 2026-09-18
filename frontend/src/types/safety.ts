export type SafetySummary = {
  total: number;
  safe: number;
  constructive: number;
  toxic: number;
  severe_abuse: number;
  spam: number;
  shielded: number;
};

export type SafetyAnalyzeResult = {
  analyzed_comments: number;
};

export type SafetyComment = {
  id: number;
  text: string;
  username: string | null;
  commented_at: string | null;
};
