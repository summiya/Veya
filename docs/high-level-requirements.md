# High-Level Requirements

## 1. Purpose

Veya is a creator-focused social sentiment and wellbeing platform. It helps creators understand audience reactions without requiring them to consume every negative or abusive comment.

## 2. Primary users

- Instagram creators
- Influencers
- Public-facing professionals
- Social media managers
- Small brands and teams

## 3. Core outcomes

Veya should help users:

1. Understand overall audience sentiment.
2. Understand sentiment for each post or reel.
3. Separate constructive criticism from harmful comments.
4. Highlight positive audience interactions.
5. Reduce unnecessary exposure to abusive or toxic content.
6. Identify recurring audience themes.
7. Track sentiment trends over time.
8. Make informed content decisions.

## 4. MVP requirements

The MVP must:

- Connect to Instagram through supported Meta APIs.
- Retrieve owned media and associated comments.
- Handle comment pagination.
- Classify comments as positive, neutral, or negative.
- Calculate sentiment percentages.
- Provide post-level sentiment.
- Provide profile-level sentiment.
- Expose backend APIs through FastAPI.
- Provide a React dashboard for viewing results.
- Persist required data in PostgreSQL.
- Run locally using Docker Compose.
- Include automated tests for critical behavior.

## 5. Non-functional requirements

### Privacy

- Do not commit access tokens or credentials.
- Store only data required for product behavior.
- Allow account disconnection.
- Support data deletion in future product phases.

### Maintainability

- Keep API, application, domain, and infrastructure concerns separated.
- Keep external providers behind interfaces.
- Avoid provider-specific logic in business services.

### Performance

- Do not use a large LLM for every comment.
- Use efficient NLP classification for per-comment sentiment.
- Use LLMs only for higher-level summaries and insights.

### Reliability

- Handle Instagram API failures gracefully.
- Handle empty comment sets.
- Handle pagination safely.
- Avoid duplicate comment ingestion.

## 6. Out of scope for MVP

- TikTok
- YouTube
- X/Twitter
- Billing
- Team workspaces
- Real-time notifications
- Redis
- Background workers
- Advanced multilingual sentiment
- LLM-generated recommendations
- Toxicity shielding automation

These can be introduced after the core sentiment pipeline is validated.
