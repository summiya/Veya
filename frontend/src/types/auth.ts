export type AuthUser = {
  uuid: string;
  email: string;
  is_active: boolean;
  created_at: string;
};

export type AuthResponse = {
  user: AuthUser;
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
};
