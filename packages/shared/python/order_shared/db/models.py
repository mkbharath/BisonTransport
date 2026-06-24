"""SQLAlchemy ORM models for the Order Intelligence Platform.

All tables match the schema defined in design.md Section 3.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


# --- Users ---


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # agent|supervisor|admin|readonly
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    cognito_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # local dev only
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Customers ---


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email_domains: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    always_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    default_equipment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    opt_out: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


# --- Emails ---


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    thread_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    to_address: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    classification_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="received")
    linked_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    attachments: Mapped[list["EmailAttachment"]] = relationship(back_populates="email")


# --- Email Attachments ---


class EmailAttachment(Base):
    __tablename__ = "email_attachments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    extracted_text_s3_key: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    ocr_confidence: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    processing_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    email: Mapped["Email"] = relationship(back_populates="attachments")


# --- Orders ---


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    source_email_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="extracted")
    overall_confidence_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    processing_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    field_confidence_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Customer Info
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_external_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Pickup
    pickup_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pickup_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pickup_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    pickup_time_window: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pickup_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Delivery
    delivery_location_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_address: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    delivery_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    delivery_time_window: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    delivery_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Shipment
    customer_order_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    po_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    commodity: Mapped[str | None] = mapped_column(Text, nullable=True)
    freight_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    total_weight: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    weight_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    dimensions: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    num_pallets: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stackable: Mapped[bool] = mapped_column(Boolean, default=False)

    # Transportation
    equipment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    truck_size: Mapped[str | None] = mapped_column(String(50), nullable=True)
    temperature_min_c: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    temperature_max_c: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    hazmat_indicator: Mapped[bool] = mapped_column(Boolean, default=False)
    hazmat_un_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    hazmat_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    special_handling_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    liftgate_required: Mapped[bool] = mapped_column(Boolean, default=False)
    team_drive_required: Mapped[bool] = mapped_column(Boolean, default=False)
    twic_card_required: Mapped[bool] = mapped_column(Boolean, default=False)

    # Additional
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachment_references: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    reviewed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_orders_status", "status"),
        Index("idx_orders_customer_id", "customer_id"),
        Index("idx_orders_pickup_date", "pickup_date"),
        Index("idx_orders_order_number", "order_number"),
    )


# --- Conversations ---


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=True
    )
    thread_message_id: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    messages: Mapped[list["ConversationMessage"]] = relationship(back_populates="conversation")


# --- Conversation Messages ---


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # inbound|outbound
    from_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    to_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("email_templates.id"), nullable=True
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivery_status: Mapped[str | None] = mapped_column(String(50), nullable=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")


# --- Validation Results ---


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    rule_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pass|fail|warning
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Order History (Immutable) ---


class OrderHistory(Base):
    __tablename__ = "order_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    previous_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    new_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    triggered_by: Mapped[str | None] = mapped_column(String(20), nullable=True)  # agent|user|system
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    detail_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Agent Execution Logs ---


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    email_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("emails.id"), nullable=True
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True
    )
    action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    error_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Audit Logs (Immutable) ---


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    actor_type: Mapped[str] = mapped_column(String(20), nullable=False)  # user|agent|system
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    old_value_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_value_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(INET, nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_actor", "actor_id", "timestamp"),
    )


# --- Business Rules ---


class BusinessRule(Base):
    __tablename__ = "business_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    field_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rule_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rule_expression: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(String(20), default="error")
    escalate_on_fail: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# --- Field Configurations ---


class FieldConfiguration(Base):
    __tablename__ = "field_configurations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False)
    is_conditional: Mapped[bool] = mapped_column(Boolean, default=False)
    conditional_depends_on: Mapped[str | None] = mapped_column(String(100), nullable=True)
    conditional_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# --- Email Templates ---


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subject_template: Mapped[str] = mapped_column(Text, nullable=False)
    body_html_template: Mapped[str] = mapped_column(Text, nullable=False)
    body_text_template: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
