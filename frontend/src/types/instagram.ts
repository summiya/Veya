export type InstagramAccount = {
  id: number;
  instagram_user_id: string;
  username: string | null;
  token_expires_at: string | null;
  created_at: string;
};

export type InstagramMedia = {
  id: number;
  instagram_media_id: string;
  media_type: string;
  caption: string | null;
  media_url: string | null;
  thumbnail_url: string | null;
  permalink: string | null;
  posted_at: string | null;
  last_synced_at: string;
};

export type InstagramSyncResult = {
  media_count: number;
  comment_count: number;
};
