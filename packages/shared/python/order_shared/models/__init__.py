"""Pydantic domain models for the Order Intelligence Platform."""

from order_shared.models.order import OrderSchema, Address, TimeWindow, FieldConfidenceScores
from order_shared.models.email import EmailRecord, EmailAttachmentRecord
from order_shared.models.agent import AgentMessage, ExtractionResult, ValidationResultModel
from order_shared.models.enums import (
    OrderStatus,
    EmailClassification,
    FreightType,
    EquipmentType,
    ProcessingMode,
    HitlQueueType,
    UserRole,
    ValidationStatus,
)

__all__ = [
    "OrderSchema",
    "Address",
    "TimeWindow",
    "FieldConfidenceScores",
    "EmailRecord",
    "EmailAttachmentRecord",
    "AgentMessage",
    "ExtractionResult",
    "ValidationResultModel",
    "OrderStatus",
    "EmailClassification",
    "FreightType",
    "EquipmentType",
    "ProcessingMode",
    "HitlQueueType",
    "UserRole",
    "ValidationStatus",
]
