"""Admin endpoints — field configs, business rules, email templates, users."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
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
    role: str
    active: bool = True


# --- Field Configurations ---


@router.get("/field-configs")
async def list_field_configs(current_user: CurrentUser = Depends(require_role("admin"))):
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM field_configurations ORDER BY display_order ASC NULLS LAST")
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
    import hashlib

    user_id = str(uuid.uuid4())
    # Default password for new users (they should change it)
    default_hash = hashlib.sha256("changeme".encode()).hexdigest()

    async with async_session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO users (id, email, name, role, active, password_hash, created_at)
                VALUES (:id, :email, :name, :role, :active, :password_hash, NOW())
            """),
            {"id": user_id, "password_hash": default_hash, **body.model_dump()},
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
    body: UserRequest,
    current_user: CurrentUser = Depends(require_role("admin")),
):
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                UPDATE users SET email = :email, name = :name, role = :role, active = :active
                WHERE id = :id RETURNING id
            """),
            {"id": user_id, **body.model_dump()},
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
