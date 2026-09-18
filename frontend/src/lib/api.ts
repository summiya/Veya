import { authStorage } from "./auth-storage";

type ApiErrorPayload = {
  detail?: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let message = "Something went wrong.";

  try {
    const body = (await response.json()) as ApiErrorPayload;
    if (body.detail) {
      message = body.detail;
    }
  } catch {
    // Keep the fallback message when the response is not JSON.
  }

  return new ApiError(message, response.status);
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");

  const accessToken = authStorage.getAccessToken();
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(path, {
    ...init,
    headers,
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
