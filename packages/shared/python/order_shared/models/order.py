"""Pydantic models for order data throughout the pipeline."""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from order_shared.models.enums import (
    EquipmentType,
    FreightType,
    OrderStatus,
    ProcessingMode,
)


class Address(BaseModel):
    """Structured address for pickup or delivery."""

    line1: str = ""
    line2: str | None = None
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = "CA"


class TimeWindow(BaseModel):
    """Time window for pickup or delivery (HH:MM format)."""

    start: str | None = None  # HH:MM
    end: str | None = None  # HH:MM


class FieldConfidenceScores(BaseModel):
    """Per-field confidence scores from extraction (0-100)."""

    model_config = {"extra": "allow"}

    # This model allows arbitrary field names as keys with float values.
    # Used as: {"customer_name": 95.0, "pickup_date": 87.5, ...}


class OrderSchema(BaseModel):
    """Complete order schema used throughout the pipeline.

    This is the canonical representation of an order as it flows
    from extraction → validation → creation.
    """

    # System fields
    id: UUID | None = None
    order_number: str | None = None
    source_email_id: UUID | None = None
    customer_id: UUID | None = None
    status: OrderStatus = OrderStatus.EXTRACTED
    overall_confidence_score: float | None = None
    processing_mode: ProcessingMode | None = None
    field_confidence_scores: dict[str, float] = Field(default_factory=dict)

    # Customer Information
    customer_name: str | None = None
    customer_external_id: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None

    # Pickup Information
    pickup_location_name: str | None = None
    pickup_address: Address | None = None
    pickup_date: date | None = None
    pickup_time_window: TimeWindow | None = None
    pickup_instructions: str | None = None

    # Delivery Information
    delivery_location_name: str | None = None
    delivery_address: Address | None = None
    delivery_date: date | None = None
    delivery_time_window: TimeWindow | None = None
    delivery_instructions: str | None = None

    # Shipment Information
    customer_order_number: str | None = None
    reference_number: str | None = None
    po_number: str | None = None
    commodity: str | None = None
    freight_type: FreightType | None = None
    total_weight: float | None = None
    weight_unit: str | None = "lbs"
    dimensions: str | None = None
    total_quantity: int | None = None
    num_pallets: int | None = None
    stackable: bool = False

    # Transportation Details
    equipment_type: EquipmentType | None = None
    truck_size: str | None = None
    temperature_min_c: float | None = None
    temperature_max_c: float | None = None
    hazmat_indicator: bool = False
    hazmat_un_number: str | None = None
    hazmat_class: str | None = None
    special_handling_instructions: str | None = None
    liftgate_required: bool = False
    team_drive_required: bool = False
    twic_card_required: bool = False

    # Additional
    notes: str | None = None
    internal_comments: str | None = None
    attachment_references: list[str] = Field(default_factory=list)

    # Audit
    reviewed_by_user_id: UUID | None = None
    reviewed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def get_mandatory_field_names(self) -> list[str]:
        """Return list of field names expected to be mandatory based on standard schema."""
        return [
            "customer_name",
            "contact_name",
            "contact_email",
            "pickup_location_name",
            "pickup_date",
            "delivery_location_name",
            "delivery_date",
            "commodity",
            "freight_type",
            "total_weight",
            "weight_unit",
            "equipment_type",
            "hazmat_indicator",
        ]

    def compute_overall_confidence(self) -> float:
        """Compute overall confidence as weighted average of mandatory field scores."""
        mandatory = self.get_mandatory_field_names()
        scores = [
            self.field_confidence_scores.get(f, 0.0)
            for f in mandatory
            if f in self.field_confidence_scores
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)
