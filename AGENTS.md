# Veya Agent Workflow

Veya is designed to be developed by coding agents and humans.

## Product principle
Help creators understand audience sentiment without forcing them to absorb unnecessary toxicity. Do not optimize for artificial positivity: preserve constructive criticism and distinguish it from abuse.

## Backend
- Python 3.12 + FastAPI.
- HTTP concerns belong in `api/`.
- Use-case orchestration belongs in `application/`.
- Business concepts belong in `domain/`.
- External systems belong in `infrastructure/`.
- Keep database access out of routes.
- Instagram integrations belong in `infrastructure/instagram/`.
- NLP/LLM providers belong in `infrastructure/ai/`.

## Frontend
- React + TypeScript + Vite.
- Keep API calls out of visual components.
- Prefer small reusable components.
- Do not surface toxic comment text by default.

## Infrastructure
- PostgreSQL is the primary database.
- SQLAlchemy is the ORM.
- Alembic owns migrations.
- Docker Compose is the local development entry point.
- Redis/workers are future infrastructure and should only be added when required.

## AI strategy
- Use a dedicated NLP model for high-volume per-comment sentiment.
- Use LLMs for higher-level summaries, themes, and insights.
- Keep LLM providers behind interfaces.

## Agent workflow
1. Read the task and relevant existing code first.
2. Make the smallest coherent change.
3. Add or update tests.
4. Run formatting, linting, tests, and relevant builds.
5. Never commit credentials or real tokens.
6. Update documentation when architecture/setup changes.
7. Keep commits focused.

## Definition of done
- Code is typed where practical.
- Tests cover changed behavior.
- Ruff passes for Python changes.
- Frontend builds for frontend changes.
- Docker configuration remains valid after infrastructure changes.
- No secrets are committed.
