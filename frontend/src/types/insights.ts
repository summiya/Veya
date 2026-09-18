export type AudienceInsight = {
  id: number;
  summary: string;
  what_people_loved: string[];
  constructive_feedback: string[];
  recurring_complaints: string[];
  common_questions: string[];
  content_suggestions: string[];
  provider: string;
  model: string;
  source_comment_count: number;
  generated_at: string;
};
