# System Architecture

## Overview

Veya is a full-stack application with a React frontend, FastAPI backend, PostgreSQL database, Instagram integration, and an NLP sentiment layer.

```text
React + TypeScript
        |
        v
      FastAPI
        |
   +----+-------------+
   |                  |
   v                  v
PostgreSQL       Instagram API
                      |
                      v
                 Comment Data
                      |
                      v
               Sentiment Engine
                      |
                      v
                  Analytics
```

## Frontend

Technology:
- React
- TypeScript
- Vite

Responsibilities:
- Authentication/connection UI
- Dashboard
- Post list
- Post details
- Sentiment visualization
- Future Positive Feed and Comment Shield

The frontend should not contain business logic or provider credentials.

## Backend

Technology:
- Python 3.12
- FastAPI
- Pydantic

Suggested layers:

```text
api/
application/
domain/
infrastructure/
repositories/
```

### API layer
HTTP routing, request validation, response models.

### Application layer
Use-case orchestration.

### Domain layer
Sentiment concepts and product rules independent of infrastructure.

### Infrastructure layer
Instagram, database, NLP, LLM, and other external systems.

### Repository layer
Persistence abstractions and implementations.

## Database

Technology:
- PostgreSQL
- SQLAlchemy
- Alembic

Initial entities may include:

- users
- instagram_accounts
- media
- comments
- comment_sentiments
- profile_snapshots
- post_analytics

## AI architecture

### Per-comment sentiment

Use a dedicated NLP classifier for:
- Positive
- Neutral
- Negative

This path should be efficient and relatively inexpensive.

### Higher-level intelligence

Future LLM capabilities:
- Theme extraction
- Constructive feedback summaries
- Common complaint summaries
- Audience insight generation

LLM providers must remain replaceable.

## Infrastructure

Local development:
- Docker Compose
- Backend container
- Frontend container
- PostgreSQL container

Future infrastructure, only when justified:
- Redis
- Background workers
- Job queues
- Scheduled synchronization

## Security

- Secrets must stay in environment variables.
- Instagram credentials must never be exposed to the browser.
- OAuth/access tokens should be encrypted at rest in production.
- Use least-privilege API permissions.
- Validate all external inputs.
