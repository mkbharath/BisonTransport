"""Shared enumerations used across all services and agents."""

from enum import StrEnum


class OrderStatus(StrEnum):
    EXTRACTED = "extracted"
    PENDING_REVIEW = "pending_review"
    AWAITING_CUSTOMER = "awaiting_customer"
    VALIDATED = "validated"
    ORDER_CREATED = "order_created"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EmailClassification(StrEnum):
    NEW_ORDER = "new_order"
    ORDER_UPDATE = "order_update"
    CUSTOMER_RESPONSE = "customer_response"
    CANCELLATION = "cancellation"
    OTHER = "other"


class FreightType(StrEnum):
    FTL = "ftl"
    LTL = "ltl"
    PARTIAL = "partial"
    INTERMODAL = "intermodal"


class EquipmentType(StrEnum):
    DRY_VAN = "dry_van"
    FLATBED = "flatbed"
    REEFER = "reefer"
    STEP_DECK = "step_deck"
    TANKER = "tanker"
    LOWBOY = "lowboy"
    CONESTOGA = "conestoga"
    OTHER = "other"


class ProcessingMode(StrEnum):
    AUTO = "auto"
    HITL_REVIEW = "hitl_review"
    MANUAL_ENTRY = "manual_entry"


class HitlQueueType(StrEnum):
    CONFIDENCE_REVIEW = "confidence_review"
    VALIDATION_FAILURE = "validation_failure"
    EXCEPTION = "exception"
    DUPLICATE_REVIEW = "duplicate_review"
    ESCALATION = "escalation"


class UserRole(StrEnum):
    READONLY = "readonly"
    AGENT = "agent"
    SUPERVISOR = "supervisor"
    ADMIN = "admin"


class ValidationStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"


class AgentType(StrEnum):
    EMAIL_INTAKE = "email_intake"
    DOCUMENT_UNDERSTANDING = "document_understanding"
    ORDER_EXTRACTION = "order_extraction"
    VALIDATION = "validation"
    COMMUNICATION = "communication"
    ORDER_CREATION = "order_creation"
