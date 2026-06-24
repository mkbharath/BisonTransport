"""Pydantic models for agent-to-agent communication via queues."""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from order_shared.models.enums import AgentType, HitlQueueType, ValidationStatus


class AgentMessage(BaseModel):
    """Envelope for messages passed between agents via SQS queues.

    Every queue message uses this envelope to carry routing metadata
    alongside the payload.
    """

    message_id: UUID = Field(default_factory=uuid4)
    source_agent: AgentType
    target_queue: str
    email_id: UUID | None = None
    order_id: UUID | None = None
    run_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    payload: dict[str, Any] = Field(default_factory=dict)

    # Routing metadata (set by Validation Agent)
    hitl_queue_type: HitlQueueType | None = None
    confidence_score: float | None = None


class ExtractionResult(BaseModel):
    """Output from the Document Understanding Agent for a single document."""

    attachment_id: UUID | None = None
    file_name: str
    file_type: str
    text_content: str
    structured_data: list[dict[str, Any]] = Field(default_factory=list)
    tables: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    source_coordinates: dict[str, Any] = Field(default_factory=dict)
    # e.g. {"page": 1, "table_index": 0, "cell": "B3"}


class ValidationResultModel(BaseModel):
    """Result of validating a single field against a business rule."""

    field_name: str
    rule_name: str | None = None
    status: ValidationStatus
    message: str | None = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now())

    @property
    def passed(self) -> bool:
        return self.status == ValidationStatus.PASS

    @property
    def failed(self) -> bool:
        return self.status == ValidationStatus.FAIL
