"""Customer management endpoints."""

import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from order_shared.db.session import async_session_factory

from order_api.auth import CurrentUser, get_current_user, require_role

router = APIRouter(prefix="/api/v1/customers", tags=["customers"])


class CustomerCreateRequest(BaseModel):
    name: str
    external_id: str | None = None
    email_domains: list[str] | None = None
    always_human_review: bool = False
    default_equipment_type: str | None = None


class CustomerUpdateRequest(BaseModel):
    name: str | None = None
    external_id: str | None = None
    email_domains: list[str] | None = None
    always_human_review: bool | None = None
    default_equipment_type: str | None = None
    opt_out: bool | None = None


@router.get("")
async def list_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List customers with search and pagination."""
    offset = (page - 1) * limit
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if search:
        conditions.append("(c.name ILIKE :search OR c.external_id ILIKE :search)")
        params["search"] = f"%{search}%"

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    async with async_session_factory() as session:
        count_result = await session.execute(
            text(f"SELECT COUNT(*) FROM customers c WHERE {where_clause}"), params
        )
        total_count = count_result.scalar() or 0

        result = await session.execute(
            text(f"""
                SELECT c.* FROM customers c
                WHERE {where_clause}
                ORDER BY c.name ASC
                LIMIT :limit OFFSET :offset
            """),
            params,
        )
        rows = [dict(r._mapping) for r in result]

    total_pages = math.ceil(total_count / limit) if total_count > 0 else 0
    return {
        "data": _serialize_rows(rows),
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "limit": limit,
    }


@router.post("", status_code=201)
async def create_customer(
    body: CustomerCreateRequest,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Create a new customer."""
    customer_id = str(uuid.uuid4())

    async with async_session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO customers (id, name, external_id, email_domains,
                    always_human_review, default_equipment_type, created_at)
                VALUES (:id, :name, :external_id, :email_domains,
                    :always_human_review, :default_equipment_type, NOW())
            """),
            {
                "id": customer_id,
                "name": body.name,
                "external_id": body.external_id,
                "email_domains": body.email_domains,
                "always_human_review": body.always_human_review,
                "default_equipment_type": body.default_equipment_type,
            },
        )
        await session.commit()

        result = await session.execute(
            text("SELECT * FROM customers WHERE id = :id"), {"id": customer_id}
        )
        customer = dict(result.mappings().first())

    return _serialize_row(customer)


@router.get("/{customer_id}")
async def get_customer(customer_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """Get customer by ID."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM customers WHERE id = :id"), {"id": customer_id}
        )
        customer = result.mappings().first()
        if not customer:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Customer not found"}},
            )
    return _serialize_row(dict(customer))


@router.patch("/{customer_id}")
async def update_customer(
    customer_id: str,
    body: CustomerUpdateRequest,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Update a customer."""
    updates = []
    params: dict = {"id": customer_id}

    for field, value in body.model_dump(exclude_unset=True).items():
        updates.append(f"{field} = :{field}")
        params[field] = value

    if not updates:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "BAD_REQUEST", "message": "No fields to update"}},
        )

    updates.append("updated_at = NOW()")

    async with async_session_factory() as session:
        set_clause = ", ".join(updates)
        result = await session.execute(
            text(f"UPDATE customers SET {set_clause} WHERE id = :id RETURNING id"), params
        )
        if not result.first():
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Customer not found"}},
            )
        await session.commit()

        result = await session.execute(
            text("SELECT * FROM customers WHERE id = :id"), {"id": customer_id}
        )
        customer = dict(result.mappings().first())

    return _serialize_row(customer)


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
