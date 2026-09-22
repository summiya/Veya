from pydantic import BaseModel


class MetaWebhookDeliveryResponse(BaseModel):
    status: str
    comment_events: int = 0
    matched_accounts: int = 0
    queued_jobs: int = 0
    ignored_events: int = 0
