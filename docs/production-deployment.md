# Production Deployment

## Goal

Veya's production runtime is split into independently observable services:

```text
Internet
   |
   v
Nginx + React
   |
   +--> /api/* --> FastAPI
                    |
          +---------+---------+
          |                   |
          v                   v
      PostgreSQL            Redis
                                |
                                v
                           ARQ Worker
```

## Production containers

`docker-compose.production.yml` contains:

- `migrate`: one-shot Alembic migration
- `backend`: non-root FastAPI image
- `worker`: ARQ worker using the same backend image
- `frontend`: compiled React assets served by Nginx
- `db`: PostgreSQL with a persistent volume
- `redis`: password-protected Redis with AOF persistence

For a managed cloud deployment, PostgreSQL and Redis can be replaced with managed services while keeping the application containers unchanged.

## Required production configuration

Start from `.env.production.example`.

The application intentionally refuses to start in `ENVIRONMENT=production` when critical development configuration remains.

Required controls include:

- JWT secret of at least 32 bytes
- HTTPS frontend URL
- HTTPS Instagram callback URL
- Instagram client ID/secret
- Instagram token encryption key
- non-console mail provider
- Resend key when using Resend

## Migrations

Migrations are a separate deployment step:

```bash
docker compose -f docker-compose.production.yml run --rm migrate
```

The production Compose stack models this as a one-shot `migrate` service. The API starts only after migration succeeds.

Do not run Alembic independently in every API replica.

## Health endpoints

### Liveness

```http
GET /health/live
```

Checks only that the FastAPI process can answer.

Use this for process/container liveness.

### Readiness

```http
GET /health/ready
```

Checks:

- PostgreSQL
- Redis

A dependency failure returns HTTP 503.

Use this endpoint for load-balancer readiness.

The legacy `GET /health` remains available as a liveness alias.

## Request IDs

Every API response contains:

```text
X-Request-ID
```

If an upstream proxy supplies an `X-Request-ID`, Veya preserves it. Otherwise Veya creates a UUID.

This ID is added to JSON request logs so an API error can be correlated across ingress/application logs.

## Structured logs

Backend and worker logs are JSON written to stdout.

Example:

```json
{
  "timestamp": "2026-09-18T18:30:00+00:00",
  "level": "INFO",
  "logger": "veya.http",
  "message": "Request completed",
  "request_id": "c3f...",
  "event": "http_request_completed",
  "method": "GET",
  "path": "/api/integrations/instagram/accounts",
  "status_code": 200,
  "duration_ms": 18.4
}
```

Worker events include job ID, attempt count, and account ID where available.

Logs deliberately do not include request bodies, JWTs, Instagram access tokens, passwords, reset tokens, or provider secrets.

## Frontend

Development uses Vite.

Production uses a multi-stage build:

```text
Node
  -> npm build
  -> static dist/
  -> Nginx
```

Nginx handles SPA fallback and proxies `/api/*` to FastAPI.

## CI

CI validates both runtime shapes:

1. Development Docker Compose.
2. Production Docker Compose.

Production CI verifies:

- production images build
- migration service completes
- FastAPI readiness succeeds
- Nginx serves React
- ARQ worker stays running
- PostgreSQL and Redis are available

## Recommended managed production topology

For a public beta, prefer:

- managed PostgreSQL
- managed Redis
- container hosting for FastAPI and ARQ worker
- CDN/static or container hosting for the React/Nginx frontend
- centralized log collection
- automated encrypted backups
- secret-manager supplied environment variables

The repository remains provider-neutral so the hosting provider can be selected later without changing application architecture.
