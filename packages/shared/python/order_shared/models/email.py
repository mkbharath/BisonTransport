"""Pydantic models for email records and attachments."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from order_shared.models.enums import EmailClassification


class EmailAttachmentRecord(BaseModel):
    """Metadata for an email attachment."""

    id: UUID | None = None
    email_id: UUID | None = None
    file_name: str
    file_type: str | None = None
    file_size_bytes: int | None = None
    s3_key: str
    extracted_text_s3_key: str | None = None
    ocr_confidence: float | None = None
    processing_status: str | None = None


class EmailRecord(BaseModel):
    """Representation of an email as it flows through the pipeline."""

    id: UUID | None = None
    message_id: str
    thread_id: str | None = None
    from_address: str
    to_address: str
    subject: str | None = None
    body_text: str | None = None
    body_html: str | None = None
    received_at: datetime
    processed_at: datetime | None = None
    classification: EmailClassification | None = None
    classification_confidence: float | None = None
    status: str = "received"
    linked_order_id: UUID | None = None
    conversation_id: UUID | None = None
    attachments: list[EmailAttachmentRecord] = []
    created_at: datetime | None = None
