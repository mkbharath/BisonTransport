"""HITL queue endpoints."""

import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from order_shared.db.session import async_session_factory

from order_api.auth import CurrentUser, get_current_user, require_role

router = APIRouter(prefix="/api/v1/queues", tags=["queues"])


@router.get("/hitl")
async def list_hitl_items(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    queue_type: str | None = None,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """List HITL review items — orders requiring human review."""
    offset = (page - 1) * limit
    conditions = ["o.status = 'pending_review'"]
    params: dict = {"limit": limit, "offset": offset}

    if queue_type:
        conditions.append("o.processing_mode = :queue_type")
        params["queue_type"] = queue_type

    where_clause = " AND ".join(conditions)

    async with async_session_factory() as session:
        count_result = await session.execute(
            text(f"SELECT COUNT(*) FROM orders o WHERE {where_clause}"), params
        )
        total_count = count_result.scalar() or 0

        result = await session.execute(
            text(f"""
                SELECT o.id, o.order_number, o.customer_name, o.status,
                       o.overall_confidence_score, o.processing_mode,
                       o.pickup_date, o.delivery_date, o.equipment_type,
                       o.created_at, o.updated_at
                FROM orders o
                WHERE {where_clause}
                ORDER BY o.overall_confidence_score ASC NULLS LAST, o.created_at ASC
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


@router.get("/hitl/{order_id}")
async def get_hitl_detail(
    order_id: str,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Get HITL review detail for an order, including validation results."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}
        )
        order = result.mappings().first()
        if not order:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Order not found"}},
            )

        val_result = await session.execute(
            text("SELECT * FROM validation_results WHERE order_id = :order_id ORDER BY evaluated_at DESC"),
            {"order_id": order_id},
        )
        validations = [dict(r._mapping) for r in val_result]

    order_data = _serialize_row(dict(order))
    order_data["validation_results"] = _serialize_rows(validations)
    return order_data


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
