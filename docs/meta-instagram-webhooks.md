# Instagram Webhooks

## Goal

Veya can receive signed Meta webhook deliveries for Instagram comment changes and use them to trigger the existing background synchronization pipeline.

The webhook does not become a second comment-ingestion path. It only tells Veya that an account changed.

```text
Instagram comment event
        |
        v
Meta webhook
        |
        v
Signature verification
        |
        v
Redis delivery deduplication
        |
        v
Existing Instagram account match
        |
        v
Existing ARQ sync pipeline
        |
        +--> media/comments refresh
        +--> pending sentiment
        +--> pending safety
        +--> analytics snapshot
```

The scheduled polling job remains enabled as a recovery/fallback mechanism.

## Endpoint

Verification and delivery use the same callback URL:

```text
GET  /api/webhooks/meta/instagram
POST /api/webhooks/meta/instagram
```

## Configuration

Enable webhooks only after the callback is reachable by Meta:

```env
META_WEBHOOK_ENABLED=true
META_WEBHOOK_VERIFY_TOKEN=<random-value-you-choose>
META_WEBHOOK_DEDUPE_SECONDS=86400
```

Webhook POST signatures are checked with HMAC SHA-256.

By default Veya reuses `INSTAGRAM_CLIENT_SECRET` as the signature secret. An optional `META_WEBHOOK_APP_SECRET` setting can override it when required.

Do not commit either secret.

## Verification handshake

When Meta verifies the callback it sends:

- `hub.mode`
- `hub.verify_token`
- `hub.challenge`

Veya returns the challenge only when:

- webhooks are enabled
- mode is `subscribe`
- verify token matches exactly

Invalid verification returns HTTP 403.

Disabled webhooks return HTTP 404.

## Delivery security

POST deliveries must include:

```text
X-Hub-Signature-256: sha256=<digest>
```

Veya computes the HMAC SHA-256 digest over the exact raw request body and compares it using a constant-time comparison.

Missing or invalid signatures return HTTP 401.

## Duplicate delivery handling

Meta may deliver the same notification more than once.

Veya hashes the raw delivery body and stores a short-lived Redis key:

```text
veya:webhooks:meta:<sha256>
```

The default retention is 24 hours.

A duplicate delivery is acknowledged with HTTP 200 but does not create another sync job.

## Comment events

For the current release, Veya reacts to the `comments` webhook field.

It intentionally does not persist raw webhook comment text. The webhook only identifies which connected Instagram account changed.

Veya then fetches authoritative media/comments using the existing Instagram API client.

This preserves:

- one ingestion path
- existing token lifecycle handling
- existing API error normalization
- existing idempotent comment upserts
- existing sentiment/safety rules
- existing analytics snapshots

## Sync coalescing

If an account is already:

- queued
- running
- retrying

a new webhook delivery does not create another simultaneous account sync.

The scheduled sync interval is also moved forward when a webhook-triggered job is created so the scheduler does not immediately duplicate the same work.

## Unsupported events

Valid, signed webhook deliveries for unsupported fields are acknowledged with HTTP 200 and ignored.

This prevents Meta from retrying deliveries Veya intentionally does not process yet.

Potential future fields include:

- mentions
- messaging events
- additional media/account changes

## Local testing

Meta requires a publicly reachable HTTPS callback for real webhook delivery.

For local development, expose the Veya backend through a secure HTTPS tunnel and point Meta's callback URL to:

```text
https://<public-host>/api/webhooks/meta/instagram
```

The public URL must forward to the local FastAPI service.

For the standard repository development ports that is normally:

```text
localhost:8000
```

If Veya is run on a different host port alongside another project, forward the public tunnel to that Veya backend port instead.

## Meta dashboard setup

After the production or tunnel URL is available:

1. Open the Meta app dashboard.
2. Configure the Instagram webhook callback URL.
3. Enter the same value configured as `META_WEBHOOK_VERIFY_TOKEN`.
4. Complete callback verification.
5. Subscribe to the Instagram `comments` field.
6. Send a Meta test delivery.
7. Confirm Veya returns HTTP 200.
8. Confirm an ARQ sync job with trigger `webhook` is created for the connected account.
9. Confirm sentiment, safety, and analytics update through the normal pipeline.

## Production behavior

Keep scheduled polling enabled even after webhooks are live.

Webhooks reduce latency; polling provides reconciliation if a delivery is delayed, missed, or intentionally ignored.

Production deployment should monitor:

- `instagram_webhook_accepted`
- `instagram_webhook_enqueue_failed`
- worker sync failures
- Instagram reconnect-required events

## External work still required

The code path is complete in the repository, but real delivery still depends on:

- a production Meta app
- a public HTTPS callback URL
- the correct verify token
- valid Instagram permissions
- webhook subscription to `comments`
- a connected Business/Creator test account
