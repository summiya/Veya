export type AudienceHealthSnapshot = {
  id: number;
  analyzed_comment_count: number;

  positive: number;
  neutral: number;
  negative: number;

  positive_percentage: number;
  neutral_percentage: number;
  negative_percentage: number;

  constructive: number;
  toxic: number;
  severe_abuse: number;
  spam: number;
  shielded: number;

  captured_at: string;
};

export type AudienceTrend = {
  points: AudienceHealthSnapshot[];
  positive_change: number | null;
  negative_change: number | null;
  shielded_change: number | null;
};
