# Error Monitoring and Alerting

## Overview

Veya supports Sentry for backend, worker, and React error monitoring.

Monitoring is disabled when the relevant DSN is blank, so local development and CI do not require a Sentry account.

## Backend and worker configuration

Configure:

```env
SENTRY_DSN=https://...
SENTRY_TRACES_SAMPLE_RATE=0.05
SENTRY_ALERT_COOLDOWN_SECONDS=300
```

Backend and worker events include:

- environment
- release
- event name
- request ID when available
- worker job ID / attempt count where relevant

Veya intentionally does not send default PII.

## Frontend configuration

The React build accepts:

```env
VITE_SENTRY_DSN=https://...
VITE_SENTRY_TRACES_SAMPLE_RATE=0.05
VITE_RELEASE=0.1.0
```

These values are build-time values because Vite embeds `VITE_*` configuration into the compiled frontend bundle.

The Sentry DSN is safe to expose to the browser; authentication secrets and provider API keys are not.

## Privacy scrubbing

Before telemetry leaves Veya, backend and frontend monitoring remove:

- request bodies
- cookies
- Authorization headers
- API-key/auth-token headers
- query strings
- user identity/PII

This specifically prevents reset tokens, passwords, JWTs, refresh tokens, and Instagram access tokens from being attached to error events.

Breadcrumb URLs also have query strings removed.

## Request correlation

FastAPI responses expose:

```text
X-Request-ID
```

The same request ID is added to backend Sentry events.

When investigating a user-reported failure:

1. Ask for the request ID if it is visible in logs/support tooling.
2. Search application logs for the request ID.
3. Search Sentry event tags for the same request ID.
4. Correlate the API exception with worker/Instagram events if applicable.

## Operational events

### http_unhandled_exception

Meaning:

An unhandled FastAPI request exception reached the global request middleware.

Action:

- inspect exception stack
- correlate request ID
- check deploy/release tag
- reproduce with the same route
- create/fix regression test

### background_sync_failed

Meaning:

A non-Instagram-specific background sync failure exhausted its retry budget.

Action:

- inspect worker exception
- inspect PostgreSQL/Redis health
- inspect job ID and attempt count
- retry only after fixing the underlying condition

### instagram_sync_failed

Meaning:

An Instagram sync failure exhausted all retry attempts.

Action:

- inspect Meta API error
- check account connection state
- check Meta rate limits/outages
- verify the account still has required permissions

### instagram_reconnect_required

Meaning:

The Instagram token is expired, revoked, or otherwise requires user authorization.

Veya already pauses scheduled sync for that account.

Action:

- creator reconnects Instagram from the dashboard
- confirm connection-health check succeeds
- confirm background sync returns to enabled

### instagram_sync_enqueue_failed

Meaning:

A due sync job could not be added to Redis/ARQ.

Action:

- inspect Redis health
- inspect worker/queue availability
- inspect the persisted sync job
- confirm the scheduler can enqueue after recovery

### readiness_degraded

Meaning:

`/health/ready` detected PostgreSQL or Redis as unavailable.

The alert is process-deduplicated for the configured cooldown period.

Action:

- check the failing dependency tag
- inspect infrastructure health
- do not treat liveness success as application readiness
- restore dependency before routing traffic back to the instance

## Recommended Sentry alert rules

Create production rules for:

1. **Unhandled application errors**
   - Environment: production
   - Trigger: new issue or regression
   - Severity: error/fatal
   - Notify: engineering alert channel/email

2. **Readiness degradation**
   - Tag: `event=readiness_degraded`
   - Severity: error
   - Notify immediately

3. **Background sync terminal failures**
   - Tag: `event=background_sync_failed` or `event=instagram_sync_failed`
   - Severity: error
   - Notify immediately

4. **Instagram reconnection required**
   - Tag: `event=instagram_reconnect_required`
   - Notify operations/product support
   - This often needs creator action rather than an engineering deploy

5. **Frontend regressions**
   - Environment: production
   - Trigger: new/regressed browser issue
   - Notify engineering

## Alert-noise controls

Veya does not emit monitoring events for every normal retry.

It reports:

- terminal worker failures
- enqueue failures
- reconnect-required states
- degraded readiness
- unhandled API/frontend exceptions

Readiness operational messages also use a cooldown to reduce repeated incidents during the same outage.

## Release workflow

Set:

```env
VITE_RELEASE=<release>
```

and keep backend `SERVICE_VERSION` aligned with the deployed release.

A future deployment pipeline can replace these with the Git commit SHA or release tag automatically.

## What remains external

The repository contains the monitoring integration, but a production Sentry project must still be created and configured outside the repository.

Required external steps:

1. Create backend and frontend Sentry projects (or a shared project if preferred).
2. Add DSNs to the production secret/config system.
3. Create the alert rules above.
4. Connect email/Slack/PagerDuty or the chosen notification destination.
5. Trigger a controlled test error in staging.
6. Confirm no sensitive request data appears in the event.
7. Confirm production alerts route to the intended responders.
