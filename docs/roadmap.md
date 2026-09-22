# Roadmap

## Phase 1 - Foundation

Status: Complete

- Python 3.12
- FastAPI
- React + TypeScript + Vite
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker Compose
- pytest
- GitHub Actions
- AGENTS.md
- Product documentation

## Phase 2 - Authentication

Status: Complete

- Sign up
- Login
- JWT access tokens
- Refresh-token rotation/revocation
- Logout
- Protected current-user endpoint
- React authentication screens

- Forgot/reset password
- Secure one-time reset tokens
- Transactional mailer abstraction
- Resend provider

## Phase 3 - Instagram Integration

Status: Complete for the current MVP

- Instagram OAuth connection
- Encrypted token persistence
- Media retrieval
- Comment retrieval
- Pagination
- Idempotent persistence
- Account-scoped APIs

- Long-lived Meta token lifecycle
- Connection health/reconnect flow
- Structured Meta API error handling

Remaining externally:
- Production Meta app configuration and App Review
- Validation with a real Business/Creator account

## Phase 4 - Sentiment MVP

Status: Complete

- Sentiment provider interface
- Positive / neutral / negative classification
- Persisted scores/confidence
- Profile sentiment
- Post sentiment
- Real dashboard data

## Phase 5 - Creator Safety

Status: Complete for baseline classifier

- Constructive criticism
- Toxicity
- Severe abuse
- Spam
- Comment Shield
- Safe/constructive feed

Remaining:
- Stronger multilingual ML safety model

## Phase 6 - AI Insights

Status: Complete for first provider

- LLM provider abstraction
- Structured audience summaries
- Loved themes
- Constructive feedback
- Recurring complaints
- Common questions
- Content suggestions
- Safe-comment-only LLM input

## Phase 7 - Historical Analytics

Status: Complete

- Audience-health snapshots
- 30-day trend API
- Positive/negative change
- Shielded-comment change
- Dashboard trend visualization

## Phase 8 - Background Synchronization

Status: Complete in this feature

- Redis
- ARQ worker
- Scheduled account synchronization
- Persisted sync jobs
- Retry/failure handling
- Last/next sync status
- Pending-only sentiment processing
- Pending-only safety processing
- Automatic audience-health snapshots
- Worker/Redis Docker CI checks

## Next Phases

### Phase 9 - Account recovery

Status: Complete

- Forgot/reset password backend
- Secure one-time reset tokens
- Mailer provider
- Resend adapter
- React recovery flow
- Session revocation after reset

Remaining notification work:
- Sync failure notifications
- Optional weekly audience digest

### Phase 10 - Model quality
- Multilingual sentiment
- Multilingual toxicity/safety
- Roman Urdu / Hinglish / Arabic evaluation
- Model quality benchmark dataset

### Phase 11 - Production readiness

Status: In progress

Complete in repository:
- Production Docker images
- One-shot migration service
- Nginx React serving
- JSON structured logging
- Request IDs
- Liveness/readiness endpoints
- Production configuration validation
- Production Docker CI smoke test

Additional production controls complete:
- Redis-backed authentication rate limiting
- Trusted proxy IP handling
- Nginx security headers
- Secret generation tooling
- PostgreSQL backup/verify/restore tooling
- Backup validation in CI

Remaining:
- Choose and configure production hosting
- Managed/off-site automated backup storage
- Cloud secret-manager integration
- Operational dashboards

Error monitoring/alerting integration complete in repository:
- Sentry FastAPI integration
- Sentry ARQ worker reporting
- Sentry React error boundary
- request-ID correlation
- privacy/secret scrubbing
- readiness degradation alerts
- terminal sync/reconnect alerts
- alert runbook

Meta webhook support complete in repository:
- verification challenge endpoint
- HMAC SHA-256 delivery validation
- Redis duplicate-delivery protection
- comment-event account matching
- webhook-triggered ARQ sync jobs
- scheduled polling retained as reconciliation fallback

External webhook setup still required:
- public HTTPS callback URL
- Meta webhook callback verification
- subscribe the production app to Instagram comments
- validate with a real Business/Creator account

External monitoring setup still required:
- create Sentry project(s)
- configure production DSNs
- create notification rules/destinations
- validate alerts in staging

### Phase 12 - Product growth
- Billing/subscriptions
- Additional social platforms
- Multiple creator/workspace roles when required
