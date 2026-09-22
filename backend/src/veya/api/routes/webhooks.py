import hashlib
import json
import logging
from typing import Annotated

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from veya.api.schemas.webhooks import MetaWebhookDeliveryResponse
from veya.application.background_sync.service import BackgroundSyncService
from veya.application.instagram.webhook_service import (
    InstagramWebhookDisabledError,
    InstagramWebhookService,
    InstagramWebhookSignatureError,
    InstagramWebhookVerificationError,
)
from veya.core.config import settings
from veya.infrastructure.database.dependencies import get_db


logger = logging.getLogger("veya.webhooks")
router = APIRouter(prefix="/api/webhooks/meta", tags=["webhooks"])


@router.get("/instagram", response_class=PlainTextResponse)
def verify_instagram_webhook(
    db: Annotated[Session, Depends(get_db)],
    mode: Annotated[str, Query(alias="hub.mode")],
    verify_token: Annotated[str, Query(alias="hub.verify_token")],
    challenge: Annotated[str, Query(alias="hub.challenge")],
) -> PlainTextResponse:
    try:
        verified_challenge = InstagramWebhookService(db).verification_challenge(
            mode=mode,
            verify_token=verify_token,
            challenge=challenge,
        )
    except InstagramWebhookDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InstagramWebhookVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    return PlainTextResponse(verified_challenge)


@router.post("/instagram", response_model=MetaWebhookDeliveryResponse)
async def receive_instagram_webhook(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    x_hub_signature_256: Annotated[
        str | None,
        Header(alias="X-Hub-Signature-256"),
    ] = None,
) -> MetaWebhookDeliveryResponse:
    body = await request.body()
    service = InstagramWebhookService(db)

    try:
        service.verify_signature(
            body=body,
            signature=x_hub_signature_256,
        )
    except InstagramWebhookDisabledError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InstagramWebhookSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        )

    delivery_hash = hashlib.sha256(body).hexdigest()
    redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))
    dedupe_key = f"veya:webhooks:meta:{delivery_hash}"
    claimed = False

    try:
        claimed = bool(
            await redis.set(
                dedupe_key,
                "1",
                ex=max(60, settings.meta_webhook_dedupe_seconds),
                nx=True,
            )
        )

        if not claimed:
            return MetaWebhookDeliveryResponse(status="duplicate")

        preparation = service.prepare_comment_sync_jobs(payload)

        queued_jobs = 0
        try:
            for job in preparation.jobs:
                enqueued = await redis.enqueue_job(
                    "sync_instagram_account",
                    job.id,
                    _job_id=f"veya-instagram-sync-{job.id}",
                )
                if enqueued is None:
                    raise RuntimeError(f"Background sync job {job.id} was not enqueued")
                queued_jobs += 1
        except Exception as exc:
            for job in preparation.jobs:
                BackgroundSyncService(db).mark_enqueue_failed(
                    job_id=job.id,
                    error_message=str(exc),
                )
            await redis.delete(dedupe_key)
            logger.exception(
                "Instagram webhook enqueue failed",
                extra={
                    "event": "instagram_webhook_enqueue_failed",
                    "error_type": type(exc).__name__,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Webhook accepted but background processing is unavailable",
            ) from exc

        logger.info(
            "Instagram webhook accepted",
            extra={
                "event": "instagram_webhook_accepted",
                "account_id": (
                    preparation.jobs[0].instagram_account_id
                    if len(preparation.jobs) == 1
                    else None
                ),
            },
        )

        return MetaWebhookDeliveryResponse(
            status="accepted",
            comment_events=preparation.comment_events,
            matched_accounts=preparation.matched_accounts,
            queued_jobs=queued_jobs,
            ignored_events=preparation.ignored_events,
        )
    finally:
        await redis.aclose()
