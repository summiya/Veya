# System Architecture

## Overview

Veya is a full-stack creator analytics platform built with React, FastAPI, PostgreSQL, Redis, ARQ workers, Instagram APIs, NLP sentiment/safety analysis, and optional LLM-powered audience insights.

```text
React + TypeScript
        |
        v
      FastAPI
        |
   +----+--------------------+
   |                         |
   v                         v
PostgreSQL                 Redis
   ^                         |
   |                         v
   |                    ARQ Worker
   |                         |
   +-----------+-------------+
               |
               v
         Instagram API
               |
               v
        Media + Comments
               |
      +--------+---------+
      |                  |
      v                  v
 Sentiment           Safety
      |                  |
      +--------+---------+
               |
               v
      Historical Analytics
```

## Frontend

Technology:
- React
- TypeScript
- Vite

Responsibilities:
- Authentication and Instagram connection
- Dashboard analytics
- Sentiment visualization
- Comment Shield and safe/constructive feed
- AI audience insights
- Historical trends
- Automatic synchronization status

The frontend contains no provider secrets or business persistence logic.

## Backend

Technology:
- Python 3.12
- FastAPI
- Pydantic
- SQLAlchemy
- Alembic

Application layers:

```text
api/
application/
domain/
infrastructure/
repositories/
```

### API layer
HTTP routing, authentication dependencies, request validation, and response models.

### Application layer
Use-case orchestration such as authentication, Instagram sync, sentiment, safety, insights, analytics, and background synchronization.

### Domain layer
Persistent business entities and product concepts.

### Infrastructure layer
Instagram API, token encryption, NLP providers, LLM providers, Redis/ARQ jobs, and database infrastructure.

### Repository layer
Persistence access isolated from controllers and application services.

## Database

Technology:
- PostgreSQL
- SQLAlchemy
- Alembic

Current major entities include:
- users
- refresh_tokens
- instagram_accounts
- instagram_media
- instagram_comments
- comment_sentiments
- comment_safety
- audience_insights
- audience_health_snapshots
- instagram_sync_jobs

## Background synchronization

Redis and ARQ provide the asynchronous job layer.

```text
ARQ scheduler
     |
     v
Due Instagram account
     |
     v
instagram_sync_jobs
     |
     v
ARQ worker
     |
     +--> Instagram media/comment upsert
     |
     +--> Pending sentiment analysis only
     |
     +--> Pending safety analysis only
     |
     +--> Audience health snapshot
     |
     v
last_synced_at / next_sync_at
```

The default account synchronization interval is 15 minutes.

The worker scheduler checks for due accounts every minute. Both the sync interval and retry behavior are environment-configurable.

ARQ may execute a job more than once after interruption, so the workflow is deliberately idempotent:
- Instagram media/comments are upserted by external IDs.
- Background sentiment only processes comments without a sentiment row.
- Background safety only processes comments without a safety row.
- Sync-job state is persisted in PostgreSQL.

### Retry behavior

A sync job moves through:

```text
queued
  -> running
  -> completed

or

queued
  -> running
  -> retrying
  -> running
  -> failed
```

Failures and attempt counts are retained for diagnostics.

## AI architecture

### High-volume classification

Dedicated providers handle per-comment classification:
- sentiment
- creator safety

### Higher-level intelligence

The LLM layer handles grouped/high-level analysis:
- audience summaries
- themes
- constructive feedback
- recurring complaints
- common questions
- content suggestions

LLM providers remain replaceable behind application interfaces.

## Local Docker environment

Docker Compose currently runs:
- FastAPI backend
- React frontend
- PostgreSQL
- Redis
- ARQ worker

The worker waits for the backend healthcheck so Alembic migrations finish before the scheduler begins querying background-sync tables.

## Security

- Secrets stay in environment variables.
- Instagram credentials never reach the browser.
- Instagram access tokens are encrypted before persistence.
- OAuth state is signed and short-lived.
- JWT refresh tokens are revocable.
- Background job APIs remain scoped to the authenticated account owner.
- Shielded comment text is not fetched by the frontend unless explicitly revealed.
