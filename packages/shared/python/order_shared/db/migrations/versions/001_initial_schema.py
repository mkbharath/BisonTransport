"""Initial schema — all tables for Order Intelligence Platform.

Revision ID: 001_initial
Revises: None
Create Date: 2026-06-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- Users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("mfa_enabled", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("cognito_sub", sa.String(255), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Customers ---
    op.create_table(
        "customers",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("external_id", sa.String(100), nullable=True),
        sa.Column("email_domains", ARRAY(sa.Text), nullable=True),
        sa.Column("always_human_review", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("default_equipment_type", sa.String(50), nullable=True),
        sa.Column("opt_out", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # --- Email Templates ---
    op.create_table(
        "email_templates",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("template_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("subject_template", sa.Text(), nullable=False),
        sa.Column("body_html_template", sa.Text(), nullable=False),
        sa.Column("body_text_template", sa.Text(), nullable=False),
        sa.Column("variables", ARRAY(sa.Text), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("updated_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Conversations ---
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", UUID(as_uuid=True), nullable=True),  # FK added after orders table
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("thread_message_id", sa.String(500), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Orders ---
    op.create_table(
        "orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_number", sa.String(50), unique=True, nullable=False),
        sa.Column("source_email_id", UUID(as_uuid=True), nullable=True),  # FK added later
        sa.Column("customer_id", UUID(as_uuid=True), sa.ForeignKey("customers.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'extracted'")),
        sa.Column("overall_confidence_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("processing_mode", sa.String(20), nullable=True),
        sa.Column("field_confidence_scores", JSONB, nullable=True),
        # Customer Info
        sa.Column("customer_name", sa.String(255), nullable=True),
        sa.Column("customer_external_id", sa.String(50), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        # Pickup
        sa.Column("pickup_location_name", sa.String(255), nullable=True),
        sa.Column("pickup_address", JSONB, nullable=True),
        sa.Column("pickup_date", sa.Date(), nullable=True),
        sa.Column("pickup_time_window", JSONB, nullable=True),
        sa.Column("pickup_instructions", sa.Text(), nullable=True),
        # Delivery
        sa.Column("delivery_location_name", sa.String(255), nullable=True),
        sa.Column("delivery_address", JSONB, nullable=True),
        sa.Column("delivery_date", sa.Date(), nullable=True),
        sa.Column("delivery_time_window", JSONB, nullable=True),
        sa.Column("delivery_instructions", sa.Text(), nullable=True),
        # Shipment
        sa.Column("customer_order_number", sa.String(100), nullable=True),
        sa.Column("reference_number", sa.String(100), nullable=True),
        sa.Column("po_number", sa.String(100), nullable=True),
        sa.Column("commodity", sa.Text(), nullable=True),
        sa.Column("freight_type", sa.String(50), nullable=True),
        sa.Column("total_weight", sa.Numeric(10, 2), nullable=True),
        sa.Column("weight_unit", sa.String(10), nullable=True),
        sa.Column("dimensions", sa.String(100), nullable=True),
        sa.Column("total_quantity", sa.Integer(), nullable=True),
        sa.Column("num_pallets", sa.Integer(), nullable=True),
        sa.Column("stackable", sa.Boolean(), server_default=sa.text("false")),
        # Transportation
        sa.Column("equipment_type", sa.String(50), nullable=True),
        sa.Column("truck_size", sa.String(50), nullable=True),
        sa.Column("temperature_min_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("temperature_max_c", sa.Numeric(5, 2), nullable=True),
        sa.Column("hazmat_indicator", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("hazmat_un_number", sa.String(10), nullable=True),
        sa.Column("hazmat_class", sa.String(50), nullable=True),
        sa.Column("special_handling_instructions", sa.Text(), nullable=True),
        sa.Column("liftgate_required", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("team_drive_required", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("twic_card_required", sa.Boolean(), server_default=sa.text("false")),
        # Additional
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("internal_comments", sa.Text(), nullable=True),
        sa.Column("attachment_references", ARRAY(sa.Text), nullable=True),
        sa.Column("reviewed_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_customer_id", "orders", ["customer_id"])
    op.create_index("idx_orders_pickup_date", "orders", ["pickup_date"])
    op.create_index("idx_orders_order_number", "orders", ["order_number"])

    # Add FK from conversations.order_id -> orders.id
    op.create_foreign_key("fk_conversations_order_id", "conversations", "orders", ["order_id"], ["id"])

    # --- Emails ---
    op.create_table(
        "emails",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("message_id", sa.String(500), unique=True, nullable=False),
        sa.Column("thread_id", sa.String(500), nullable=True),
        sa.Column("from_address", sa.String(255), nullable=False),
        sa.Column("to_address", sa.String(255), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("classification", sa.String(50), nullable=True),
        sa.Column("classification_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default=sa.text("'received'")),
        sa.Column("linked_order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Add FK from orders.source_email_id -> emails.id
    op.create_foreign_key("fk_orders_source_email_id", "orders", "emails", ["source_email_id"], ["id"])

    # --- Email Attachments ---
    op.create_table(
        "email_attachments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email_id", UUID(as_uuid=True), sa.ForeignKey("emails.id"), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_type", sa.String(50), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("s3_key", sa.String(1000), nullable=False),
        sa.Column("extracted_text_s3_key", sa.String(1000), nullable=True),
        sa.Column("ocr_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("processing_status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Conversation Messages ---
    op.create_table(
        "conversation_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("from_address", sa.String(255), nullable=True),
        sa.Column("to_address", sa.String(255), nullable=True),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("template_id", UUID(as_uuid=True), sa.ForeignKey("email_templates.id"), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivery_status", sa.String(50), nullable=True),
    )

    # --- Validation Results ---
    op.create_table(
        "validation_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("rule_name", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Order History (Immutable) ---
    op.create_table(
        "order_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=False),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("previous_status", sa.String(50), nullable=True),
        sa.Column("new_status", sa.String(50), nullable=True),
        sa.Column("triggered_by", sa.String(20), nullable=True),
        sa.Column("actor_id", sa.String(255), nullable=True),
        sa.Column("detail_json", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Agent Execution Logs ---
    op.create_table(
        "agent_execution_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_type", sa.String(100), nullable=False),
        sa.Column("run_id", UUID(as_uuid=True), nullable=False),
        sa.Column("email_id", UUID(as_uuid=True), sa.ForeignKey("emails.id"), nullable=True),
        sa.Column("order_id", UUID(as_uuid=True), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("action", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("llm_model", sa.String(100), nullable=True),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Audit Logs (Immutable) ---
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("actor_type", sa.String(20), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=True),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=True),
        sa.Column("old_value_json", JSONB, nullable=True),
        sa.Column("new_value_json", JSONB, nullable=True),
        sa.Column("ip_address", INET, nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
    )
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_logs_actor", "audit_logs", ["actor_id", "timestamp"])

    # --- Business Rules ---
    op.create_table(
        "business_rules",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("rule_name", sa.String(100), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=True),
        sa.Column("rule_type", sa.String(50), nullable=True),
        sa.Column("rule_expression", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), server_default=sa.text("'error'")),
        sa.Column("escalate_on_fail", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("priority", sa.Integer(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- Field Configurations ---
    op.create_table(
        "field_configurations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("field_name", sa.String(100), unique=True, nullable=False),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("is_conditional", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("conditional_depends_on", sa.String(100), nullable=True),
        sa.Column("conditional_value", sa.String(255), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true")),
    )

    # --- Order number sequence (resets daily via application logic) ---
    op.execute("CREATE SEQUENCE IF NOT EXISTS order_number_seq START 1")


def downgrade() -> None:
    op.execute("DROP SEQUENCE IF EXISTS order_number_seq")
    op.drop_table("field_configurations")
    op.drop_table("business_rules")
    op.drop_table("audit_logs")
    op.drop_table("agent_execution_logs")
    op.drop_table("order_history")
    op.drop_table("validation_results")
    op.drop_table("conversation_messages")
    op.drop_table("email_attachments")
    op.drop_table("emails")
    op.execute("ALTER TABLE conversations DROP CONSTRAINT IF EXISTS fk_conversations_order_id")
    op.execute("ALTER TABLE orders DROP CONSTRAINT IF EXISTS fk_orders_source_email_id")
    op.drop_table("orders")
    op.drop_table("conversations")
    op.drop_table("email_templates")
    op.drop_table("customers")
    op.drop_table("users")
    op.execute("DROP EXTENSION IF EXISTS vector")
