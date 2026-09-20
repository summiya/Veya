import * as Sentry from "@sentry/react";

function stripQuery(value?: string): string | undefined {
  if (!value) {
    return value;
  }

  return value.split("?", 1)[0];
}

export function scrubFrontendEvent<T extends Sentry.Event>(event: T): T {
  if (event.request) {
    event.request.url = stripQuery(event.request.url);
    event.request.query_string = "";
    event.request.data = undefined;
    event.request.cookies = undefined;

    if (event.request.headers) {
      const safeHeaders: Record<string, string> = {};

      Object.entries(event.request.headers).forEach(([key, value]) => {
        const normalized = key.toLowerCase();
        if (
          !["authorization", "cookie", "x-api-key", "x-auth-token"].includes(
            normalized,
          )
        ) {
          safeHeaders[key] = String(value);
        }
      });

      event.request.headers = safeHeaders;
    }
  }

  event.user = undefined;
  return event;
}

export function scrubFrontendBreadcrumb(
  breadcrumb: Sentry.Breadcrumb,
): Sentry.Breadcrumb {
  if (breadcrumb.data) {
    if (typeof breadcrumb.data.url === "string") {
      breadcrumb.data.url = stripQuery(breadcrumb.data.url);
    }

    [
      "authorization",
      "cookie",
      "password",
      "token",
      "access_token",
      "refresh_token",
    ].forEach((key) => {
      if (key in breadcrumb.data!) {
        breadcrumb.data![key] = "[Filtered]";
      }
    });
  }

  return breadcrumb;
}

export function initializeFrontendMonitoring(): boolean {
  const dsn = import.meta.env.VITE_SENTRY_DSN?.trim();

  if (!dsn) {
    return false;
  }

  const parsedSampleRate = Number(
    import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE ?? "0.05",
  );
  const tracesSampleRate = Number.isFinite(parsedSampleRate)
    ? Math.max(0, Math.min(1, parsedSampleRate))
    : 0.05;

  Sentry.init({
    dsn,
    environment: import.meta.env.VITE_ENVIRONMENT || import.meta.env.MODE,
    release: import.meta.env.VITE_RELEASE || undefined,
    tracesSampleRate,
    sendDefaultPii: false,
    beforeSend: scrubFrontendEvent,
    beforeBreadcrumb: scrubFrontendBreadcrumb,
  });

  return true;
}

export function captureFrontendError(
  error: unknown,
  context?: Record<string, string>,
): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN?.trim();

  if (!dsn) {
    return;
  }

  Sentry.withScope((scope) => {
    Object.entries(context ?? {}).forEach(([key, value]) => {
      scope.setTag(key, value);
    });
    Sentry.captureException(error);
  });
}
