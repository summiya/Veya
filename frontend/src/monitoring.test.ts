import { describe, expect, it } from "vitest";

import {
  scrubFrontendBreadcrumb,
  scrubFrontendEvent,
} from "./monitoring";


describe("frontend monitoring scrubbing", () => {
  it("removes query strings, request data, and PII", () => {
    const event = scrubFrontendEvent({
      request: {
        url: "https://app.example.com/reset-password?token=secret-token",
        query_string: "token=secret-token",
        data: { password: "secret" },
        cookies: { session: "secret" },
        headers: {
          Authorization: "Bearer secret",
          "X-Request-ID": "request-1",
        },
      },
      user: {
        email: "creator@example.com",
      },
    });

    expect(event.request?.url).toBe(
      "https://app.example.com/reset-password",
    );
    expect(event.request?.query_string).toBe("");
    expect(event.request?.data).toBeUndefined();
    expect(event.request?.cookies).toBeUndefined();
    expect(event.request?.headers?.Authorization).toBeUndefined();
    expect(event.request?.headers?.["X-Request-ID"]).toBe("request-1");
    expect(event.user).toBeUndefined();
  });

  it("removes tokens from breadcrumbs", () => {
    const breadcrumb = scrubFrontendBreadcrumb({
      data: {
        url: "https://app.example.com/reset-password?token=secret",
        access_token: "secret",
      },
    });

    expect(breadcrumb.data?.url).toBe(
      "https://app.example.com/reset-password",
    );
    expect(breadcrumb.data?.access_token).toBe("[Filtered]");
  });
});
