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

Remaining:
- Forgot-password backend/email delivery

## Phase 3 - Instagram Integration

Status: Complete for the current MVP

- Instagram OAuth connection
- Encrypted token persistence
- Media retrieval
- Comment retrieval
- Pagination
- Idempotent persistence
- Account-scoped APIs

Remaining:
- Production Meta app configuration
- Broader rate-limit/error telemetry

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

### Phase 9 - Account recovery and notifications
- Forgot/reset password backend
- Mailer provider
- Sync failure notifications
- Optional weekly audience digest

### Phase 10 - Model quality
- Multilingual sentiment
- Multilingual toxicity/safety
- Roman Urdu / Hinglish / Arabic evaluation
- Model quality benchmark dataset

### Phase 11 - Production readiness
- Production deployment
- Observability
- Rate limiting
- Database backups
- Secret/key management
- Meta webhook support
- Operational dashboards

### Phase 12 - Product growth
- Billing/subscriptions
- Additional social platforms
- Multiple creator/workspace roles when required
