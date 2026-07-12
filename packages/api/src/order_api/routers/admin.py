"""Admin endpoints — field configs, business rules, email templates, users."""

import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from order_shared.db.session import async_session_factory

from order_api.auth import CurrentUser, require_role

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# --- Request Models ---


class FieldConfigRequest(BaseModel):
    field_name: str
    label: str
    is_mandatory: bool = False
    is_conditional: bool = False
    conditional_depends_on: str | None = None
    conditional_value: str | None = None
    display_order: int | None = None
    active: bool = True


class BusinessRuleRequest(BaseModel):
    rule_name: str
    field_name: str | None = None
    rule_type: str | None = None
    rule_expression: str
    error_message: str | None = None
    severity: str = "error"
    escalate_on_fail: bool = False
    active: bool = True
    priority: int = 0


class EmailTemplateRequest(BaseModel):
    template_type: str
    name: str
    subject_template: str
    body_html_template: str
    body_text_template: str
    variables: list[str] | None = None
    active: bool = True


class UserRequest(BaseModel):
    email: str
    name: str
    password: str | None = None
    role: str
    active: bool = True


class UserUpdateRequest(BaseModel):
    email: str | None = None
    name: str | None = None
    password: str | None = None
    role: str | None = None
    active: bool | None = None


# --- Field Configurations ---


@router.get("/field-configs")
async def list_field_configs(current_user: CurrentUser = Depends(require_role("admin"))):
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM field_configurations ORDER BY display_order ASC NULLS LAST")
        )
        rows = [dict(r._mapping) for r in result]
    return {"data": _serialize_rows(rows)}


@router.get("/field-configs/active")
async def list_active_field_configs(current_user: CurrentUser = Depends(require_role("agent"))):
    """Get active field configurations for form rendering (agent+ accessible)."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM field_configurations WHERE active = true ORDER BY display_order ASC NULLS LAST")
        )
        rows = [dict(r._mapping) for r in result]
    return {"data": _serialize_rows(rows)}


@router.post("/field-configs", status_code=201)
async def create_field_config(
    body: FieldConfigRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    config_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO field_configurations (id, field_name, label, is_mandatory,
                    is_conditional, conditional_depends_on, conditional_value, display_order, active)
                VALUES (:id, :field_name, :label, :is_mandatory,
                    :is_conditional, :conditional_depends_on, :conditional_value, :display_order, :active)
            """),
            {"id": config_id, **body.model_dump()},
        )
        await session.commit()
        result = await session.execute(
            text("SELECT * FROM field_configurations WHERE id = :id"), {"id": config_id}
        )
        row = dict(result.mappings().first())
    return _serialize_row(row)


@router.patch("/field-configs/{config_id}")
async def update_field_config(
    config_id: str,
    body: FieldConfigRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                UPDATE field_configurations
                SET field_name = :field_name, label = :label, is_mandatory = :is_mandatory,
                    is_conditional = :is_conditional, conditional_depends_on = :conditional_depends_on,
                    conditional_value = :conditional_value, display_order = :display_order, active = :active
                WHERE id = :id RETURNING id
            """),
            {"id": config_id, **body.model_dump()},
        )
        if not result.first():
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Field config not found"}})
        await session.commit()
        result = await session.execute(
            text("SELECT * FROM field_configurations WHERE id = :id"), {"id": config_id}
        )
        row = dict(result.mappings().first())
    return _serialize_row(row)


@router.delete("/field-configs/{config_id}", status_code=204)
async def delete_field_config(
    config_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    async with async_session_factory() as session:
        result = await session.execute(
            text("DELETE FROM field_configurations WHERE id = :id RETURNING id"),
            {"id": config_id},
        )
        if not result.first():
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Field config not found"}})
        await session.commit()
    return None


# --- Business Rules ---


@router.get("/business-rules")
async def list_business_rules(current_user: CurrentUser = Depends(require_role("admin"))):
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM business_rules ORDER BY priority ASC")
        )
        rows = [dict(r._mapping) for r in result]
    return {"data": _serialize_rows(rows)}


@router.post("/business-rules", status_code=201)
async def create_business_rule(
    body: BusinessRuleRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    rule_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO business_rules (id, rule_name, field_name, rule_type,
                    rule_expression, error_message, severity, escalate_on_fail, active, priority, created_by, updated_at)
                VALUES (:id, :rule_name, :field_name, :rule_type,
                    :rule_expression, :error_message, :severity, :escalate_on_fail, :active, :priority, :created_by, NOW())
            """),
            {"id": rule_id, "created_by": current_user.id, **body.model_dump()},
        )
        await session.commit()
        result = await session.execute(
            text("SELECT * FROM business_rules WHERE id = :id"), {"id": rule_id}
        )
        row = dict(result.mappings().first())
    return _serialize_row(row)


@router.patch("/business-rules/{rule_id}")
async def update_business_rule(
    rule_id: str,
    body: BusinessRuleRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                UPDATE business_rules
                SET rule_name = :rule_name, field_name = :field_name, rule_type = :rule_type,
                    rule_expression = :rule_expression, error_message = :error_message,
                    severity = :severity, escalate_on_fail = :escalate_on_fail,
                    active = :active, priority = :priority, updated_at = NOW()
                WHERE id = :id RETURNING id
            """),
            {"id": rule_id, **body.model_dump()},
        )
        if not result.first():
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Business rule not found"}})
        await session.commit()
        result = await session.execute(
            text("SELECT * FROM business_rules WHERE id = :id"), {"id": rule_id}
        )
        row = dict(result.mappings().first())
    return _serialize_row(row)


@router.delete("/business-rules/{rule_id}", status_code=204)
async def delete_business_rule(
    rule_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    async with async_session_factory() as session:
        result = await session.execute(
            text("DELETE FROM business_rules WHERE id = :id RETURNING id"),
            {"id": rule_id},
        )
        if not result.first():
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Business rule not found"}})
        await session.commit()
    return None


# --- Email Templates ---


@router.get("/email-templates")
async def list_email_templates(current_user: CurrentUser = Depends(require_role("admin"))):
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM email_templates ORDER BY name ASC")
        )
        rows = [dict(r._mapping) for r in result]
    return {"data": _serialize_rows(rows)}


@router.post("/email-templates", status_code=201)
async def create_email_template(
    body: EmailTemplateRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    template_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO email_templates (id, template_type, name, subject_template,
                    body_html_template, body_text_template, variables, active, updated_by, updated_at)
                VALUES (:id, :template_type, :name, :subject_template,
                    :body_html_template, :body_text_template, :variables, :active, :updated_by, NOW())
            """),
            {"id": template_id, "updated_by": current_user.id, **body.model_dump()},
        )
        await session.commit()
        result = await session.execute(
            text("SELECT * FROM email_templates WHERE id = :id"), {"id": template_id}
        )
        row = dict(result.mappings().first())
    return _serialize_row(row)


@router.patch("/email-templates/{template_id}")
async def update_email_template(
    template_id: str,
    body: EmailTemplateRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                UPDATE email_templates
                SET template_type = :template_type, name = :name, subject_template = :subject_template,
                    body_html_template = :body_html_template, body_text_template = :body_text_template,
                    variables = :variables, active = :active, updated_by = :updated_by, updated_at = NOW()
                WHERE id = :id RETURNING id
            """),
            {"id": template_id, "updated_by": current_user.id, **body.model_dump()},
        )
        if not result.first():
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Email template not found"}})
        await session.commit()
        result = await session.execute(
            text("SELECT * FROM email_templates WHERE id = :id"), {"id": template_id}
        )
        row = dict(result.mappings().first())
    return _serialize_row(row)


@router.delete("/email-templates/{template_id}", status_code=204)
async def delete_email_template(
    template_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    async with async_session_factory() as session:
        result = await session.execute(
            text("DELETE FROM email_templates WHERE id = :id RETURNING id"),
            {"id": template_id},
        )
        if not result.first():
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Email template not found"}})
        await session.commit()
    return None


# --- Users ---


@router.get("/users")
async def list_users(current_user: CurrentUser = Depends(require_role("admin"))):
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT id, email, name, role, active, last_login_at, created_at FROM users ORDER BY name ASC")
        )
        rows = [dict(r._mapping) for r in result]
    return {"data": _serialize_rows(rows)}


@router.post("/users", status_code=201)
async def create_user(
    body: UserRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    from order_api.auth import hash_password

    user_id = str(uuid.uuid4())
    password = body.password or "changeme"
    password_hash = hash_password(password)

    async with async_session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, name, role, active, password_hash, created_at)
                VALUES (:id, :email, :name, :role, :active, :password_hash, NOW())
            """),
            {
                "id": user_id,
                "email": body.email,
                "name": body.name,
                "role": body.role,
                "active": body.active,
                "password_hash": password_hash,
            },
        )
        await session.commit()
        result = await session.execute(
            text("SELECT id, email, name, role, active, created_at FROM users WHERE id = :id"),
            {"id": user_id},
        )
        row = dict(result.mappings().first())
    return _serialize_row(row)


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    body: UserUpdateRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    import hashlib
    from order_api.auth import hash_password

    updates = []
    params: dict = {"id": user_id}

    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "password" and value is not None:
            # Hash the new password with bcrypt
            updates.append("password_hash = :password_hash")
            params["password_hash"] = hash_password(value)
        elif field != "password":
            updates.append(f"{field} = :{field}")
            params[field] = value

    if not updates:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "BAD_REQUEST", "message": "No fields to update"}},
        )

    set_clause = ", ".join(updates)

    async with async_session_factory() as session:
        result = await session.execute(
            text(f"UPDATE users SET {set_clause} WHERE id = :id RETURNING id"),
            params,
        )
        if not result.first():
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "User not found"}})
        await session.commit()
        result = await session.execute(
            text("SELECT id, email, name, role, active, created_at FROM users WHERE id = :id"),
            {"id": user_id},
        )
        row = dict(result.mappings().first())
    return _serialize_row(row)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    async with async_session_factory() as session:
        result = await session.execute(
            text("UPDATE users SET active = false WHERE id = :id RETURNING id"),
            {"id": user_id},
        )
        if not result.first():
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "User not found"}})
        await session.commit()
    return None


# --- Audit Logs ---


@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = None,
    actor_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    tab: str | None = None,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """List combined audit logs from order_history table."""
    offset = (page - 1) * limit
    params: dict = {"limit": limit, "offset": offset}

    conditions: list[str] = []
    if search:
        conditions.append(
            "(event_type ILIKE :search OR actor_id ILIKE :search OR triggered_by ILIKE :search)"
        )
        params["search"] = f"%{search}%"
    if actor_type and actor_type != "all":
        conditions.append("triggered_by = :actor_type")
        params["actor_type"] = actor_type
    if date_from:
        conditions.append("created_at >= :date_from::timestamptz")
        params["date_from"] = date_from
    if date_to:
        conditions.append("created_at <= :date_to::timestamptz")
        params["date_to"] = date_to
    if tab and tab != "all":
        if tab == "agent_actions":
            conditions.append("triggered_by = 'agent'")
        elif tab == "user_actions":
            conditions.append("triggered_by = 'user'")
        elif tab == "order_history":
            conditions.append("event_type ILIKE '%status%'")
        elif tab == "validations":
            conditions.append("event_type ILIKE '%valid%'")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    async with async_session_factory() as session:
        count_result = await session.execute(
            text(f"SELECT COUNT(*) FROM order_history WHERE {where_clause}"), params
        )
        total_count = count_result.scalar() or 0

        result = await session.execute(
            text(f"""
                SELECT id, created_at as timestamp, triggered_by as actor_type,
                    actor_id, event_type as action, 'order' as entity_type,
                    order_id as entity_id, previous_status, new_status, detail_json
                FROM order_history
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]

    total_pages = math.ceil(total_count / limit) if total_count > 0 else 1
    return {
        "data": _serialize_rows(rows),
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "limit": limit,
    }


# --- Helpers ---


def _serialize_row(row: dict) -> dict:
    result = {}
    for k, v in row.items():
        if isinstance(v, uuid.UUID):
            result[k] = str(v)
        elif isinstance(v, datetime):
            result[k] = v.isoformat()
        elif hasattr(v, "__class__") and v.__class__.__name__ == "Decimal":
            result[k] = float(v)
        else:
            result[k] = v
    return result


def _serialize_rows(rows: list[dict]) -> list[dict]:
    return [_serialize_row(r) for r in rows]


# --- System Config (Thresholds) ---


@router.get("/thresholds")
async def get_thresholds(current_user: CurrentUser = Depends(require_role("agent"))):
    """Get all threshold configurations."""
    async with async_session_factory() as session:
        # Try to read from system_config table
        try:
            result = await session.execute(
                text("SELECT key, value FROM system_config WHERE category = 'threshold'")
            )
            rows = {r["key"]: float(r["value"]) for r in result.mappings()}
        except Exception:
            rows = {}

    # Merge with defaults (env vars as fallback)
    import os
    defaults = {
        "AUTO_PROCESS": float(os.environ.get("THRESHOLD_AUTO_PROCESS", "95")),
        "HUMAN_REVIEW": float(os.environ.get("THRESHOLD_HUMAN_REVIEW", "80")),
        "AUTO_COMMUNICATION": float(os.environ.get("THRESHOLD_AUTO_COMMUNICATION", "70")),
        "CUSTOMER_RESPONSE_TIMEOUT_HOURS": float(os.environ.get("CUSTOMER_RESPONSE_TIMEOUT_HOURS", "48")),
        "FOLLOWUP_DELAY_HOURS": float(os.environ.get("FOLLOWUP_DELAY_HOURS", "24")),
        "DUPLICATE_DETECTION_WINDOW_HOURS": float(os.environ.get("DUPLICATE_DETECTION_WINDOW_HOURS", "72")),
    }
    # DB values override defaults
    merged = {**defaults, **rows}
    return {"data": merged}


@router.put("/thresholds")
async def update_thresholds(
    body: dict,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """Update threshold configurations. Stored in system_config table."""
    async with async_session_factory() as session:
        # Create table if not exists
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS system_config (
                key VARCHAR(100) PRIMARY KEY,
                value VARCHAR(255) NOT NULL,
                category VARCHAR(50) NOT NULL DEFAULT 'threshold',
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        for key, value in body.items():
            if key == "data":
                continue
            await session.execute(text("""
                INSERT INTO system_config (key, value, category, updated_at)
                VALUES (:key, :value, 'threshold', NOW())
                ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = NOW()
            """), {"key": key, "value": str(value)})

        await session.commit()
    return {"message": "Thresholds updated successfully"}


# --- Notifications ---


@router.get("/notifications")
async def get_notifications(
    limit: int = Query(10, ge=1, le=50),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get recent order events as notifications."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                SELECT oh.id, oh.order_id, oh.event_type, oh.new_status, oh.triggered_by,
                       oh.actor_id, oh.detail_json, oh.created_at,
                       o.order_number, o.customer_name
                FROM order_history oh
                JOIN orders o ON o.id = oh.order_id
                ORDER BY oh.created_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        )
        rows = [dict(r._mapping) for r in result]
    return {"data": _serialize_rows(rows)}


# --- Webhooks ---


class WebhookRequest(BaseModel):
    url: str
    events: list[str]  # e.g. ["order_created", "order.approved", "order.rejected"]
    active: bool = True
    secret: str | None = None


@router.get("/webhooks")
async def list_webhooks(current_user: CurrentUser = Depends(require_role("admin"))):
    """List configured webhooks."""
    async with async_session_factory() as session:
        # Ensure table exists
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                url VARCHAR(500) NOT NULL,
                events TEXT[] NOT NULL,
                active BOOLEAN DEFAULT true,
                secret VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await session.commit()
        result = await session.execute(text("SELECT * FROM webhooks ORDER BY created_at DESC"))
        rows = [dict(r._mapping) for r in result]
    return {"data": _serialize_rows(rows)}


@router.post("/webhooks", status_code=201)
async def create_webhook(
    body: WebhookRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """Create a new webhook endpoint."""
    webhook_id = str(uuid.uuid4())
    async with async_session_factory() as session:
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS webhooks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                url VARCHAR(500) NOT NULL,
                events TEXT[] NOT NULL,
                active BOOLEAN DEFAULT true,
                secret VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))
        await session.execute(
            text("""
                INSERT INTO webhooks (id, url, events, active, secret, created_at)
                VALUES (:id, :url, :events, :active, :secret, NOW())
            """),
            {"id": webhook_id, "url": body.url, "events": body.events, "active": body.active, "secret": body.secret},
        )
        await session.commit()
    return {"id": webhook_id, "url": body.url, "events": body.events, "active": body.active}


@router.delete("/webhooks/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: str,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    """Delete a webhook."""
    async with async_session_factory() as session:
        await session.execute(text("DELETE FROM webhooks WHERE id = :id"), {"id": webhook_id})
        await session.commit()
    return None
