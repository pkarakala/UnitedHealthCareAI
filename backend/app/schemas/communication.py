from pydantic import BaseModel
from datetime import datetime


class CommunicationCreate(BaseModel):
    prior_auth_id: str
    channel: str
    recipient: str
    subject: str | None = None
    body: str | None = None
    direction: str = "outbound"


class CommunicationRead(BaseModel):
    id: str
    prior_auth_id: str
    channel: str
    direction: str
    recipient: str
    subject: str | None = None
    body: str | None = None
    status: str
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationPayload(BaseModel):
    patient_id: str
    prior_auth_id: str
    channel: str
    template: str
    variables: dict = {}
