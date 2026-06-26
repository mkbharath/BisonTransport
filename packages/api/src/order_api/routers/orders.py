"""Order management endpoints."""

import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from order_shared.adapters import get_adapters
from order_shared.adapters.base import Event
from order_shared.db.session import async_session_factory

from order_api.auth import CurrentUser, get_current_user, require_role

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


# --- Request/Response Models ---


class OrderCreateRequest(BaseModel):
    customer_id: str | None = None
    customer_name: str | None = None
    pickup_address: dict | None = None
    pickup_date: str | None = None
    delivery_address: dict | None = None
    delivery_date: str | None = None
    commodity: str | None = None
    equipment_type: str | None = None
    total_weight: float | None = None
    weight_unit: str | None = None
    notes: str | None = None


class OrderUpdateRequest(BaseModel):
    status: str | None = None
    customer_name: str | None = None
    pickup_address: dict | None = None
    pickup_date: str | None = None
    delivery_address: dict | None = None
    delivery_date: str | None = None
    commodity: str | None = None
    equipment_type: str | None = None
    total_weight: float | None = None
    notes: str | None = None
    internal_comments: str | None = None


class ApproveRejectRequest(BaseModel):
    comments: str | None = None


# --- Endpoints ---


@router.get("")
async def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    customer_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    confidence_min: float | None = None,
    confidence_max: float | None = None,
    processing_mode: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List orders with pagination and filtering."""
    offset = (page - 1) * limit
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if status:
        conditions.append("o.status = :status")
        params["status"] = status
    if customer_id:
        conditions.append("o.customer_id = :customer_id")
        params["customer_id"] = customer_id
    if date_from:
        conditions.append("o.pickup_date >= :date_from")
        params["date_from"] = date_from
    if date_to:
        conditions.append("o.pickup_date <= :date_to")
        params["date_to"] = date_to
    if confidence_min is not None:
        conditions.append("o.overall_confidence_score >= :confidence_min")
        params["confidence_min"] = confidence_min
    if confidence_max is not None:
        conditions.append("o.overall_confidence_score <= :confidence_max")
        params["confidence_max"] = confidence_max
    if processing_mode:
        conditions.append("o.processing_mode = :processing_mode")
        params["processing_mode"] = processing_mode

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    async with async_session_factory() as session:
        count_q = f"SELECT COUNT(*) FROM orders o WHERE {where_clause}"
        count_result = await session.execute(text(count_q), params)
        total_count = count_result.scalar() or 0

        data_q = f"""
            SELECT o.* FROM orders o
            WHERE {where_clause}
            ORDER BY o.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        result = await session.execute(text(data_q), params)
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
async def create_order(
    body: OrderCreateRequest,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Create a new order manually."""
    order_id = str(uuid.uuid4())
    order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    async with async_session_factory() as session:
        await session.execute(
            text("""
                INSERT INTO orders (id, order_number, customer_id, customer_name,
                    pickup_address, pickup_date, delivery_address, delivery_date,
                    commodity, equipment_type, total_weight, weight_unit, notes,
                    status, processing_mode, created_at)
                VALUES (:id, :order_number, :customer_id, :customer_name,
                    :pickup_address::jsonb, :pickup_date, :delivery_address::jsonb, :delivery_date,
                    :commodity, :equipment_type, :total_weight, :weight_unit, :notes,
                    'extracted', 'manual', NOW())
            """),
            {
                "id": order_id,
                "order_number": order_number,
                "customer_id": body.customer_id,
                "customer_name": body.customer_name,
                "pickup_address": _json_or_none(body.pickup_address),
                "pickup_date": body.pickup_date,
                "delivery_address": _json_or_none(body.delivery_address),
                "delivery_date": body.delivery_date,
                "commodity": body.commodity,
                "equipment_type": body.equipment_type,
                "total_weight": body.total_weight,
                "weight_unit": body.weight_unit,
                "notes": body.notes,
            },
        )
        await session.commit()

        result = await session.execute(
            text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}
        )
        order = dict(result.mappings().first())

    return _serialize_row(order)


@router.get("/{order_id}")
async def get_order(order_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """Get order by ID."""
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
    return _serialize_row(dict(order))


@router.patch("/{order_id}")
async def update_order(
    order_id: str,
    body: OrderUpdateRequest,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Update an order's fields."""
    updates = []
    params: dict = {"id": order_id}

    for field, value in body.model_dump(exclude_unset=True).items():
        if field in ("pickup_address", "delivery_address") and value is not None:
            updates.append(f"{field} = :{field}::jsonb")
            params[field] = _json_or_none(value)
        else:
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
        await session.execute(
            text(f"UPDATE orders SET {set_clause} WHERE id = :id"), params
        )
        await session.commit()

        result = await session.execute(
            text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}
        )
        order = result.mappings().first()
        if not order:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Order not found"}},
            )
    return _serialize_row(dict(order))


@router.delete("/{order_id}", status_code=204)
async def delete_order(
    order_id: str,
    current_user: CurrentUser = Depends(require_role("supervisor")),
):
    """Soft-delete an order by setting status to 'cancelled'."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("UPDATE orders SET status = 'cancelled', updated_at = NOW() WHERE id = :id RETURNING id"),
            {"id": order_id},
        )
        if not result.first():
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Order not found"}},
            )
        await session.commit()
    return None


@router.post("/{order_id}/approve")
async def approve_order(
    order_id: str,
    body: ApproveRejectRequest | None = None,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Approve an order — moves it to 'order_created' and publishes event."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                UPDATE orders
                SET status = 'order_created', reviewed_by_user_id = :user_id,
                    reviewed_at = NOW(), updated_at = NOW()
                WHERE id = :id AND status IN ('extracted', 'validated', 'pending_review')
                RETURNING id, status
            """),
            {"id": order_id, "user_id": current_user.id},
        )
        row = result.first()
        if not row:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_STATE",
                        "message": "Order not found or not in approvable state",
                    }
                },
            )
        await session.commit()

        # Record history
        await session.execute(
            text("""
                INSERT INTO order_history (id, order_id, event_type, new_status, triggered_by, actor_id, created_at)
                VALUES (gen_random_uuid(), :order_id, 'order.approved', 'order_created', 'user', :actor_id, NOW())
            """),
            {"order_id": order_id, "actor_id": current_user.id},
        )
        await session.commit()

    # Publish event
    try:
        adapters = get_adapters()
        await adapters.events.publish_event(
            Event(
                source="order-api",
                detail_type="hitl.approved",
                detail={"order_id": order_id, "approved_by": current_user.id},
            )
        )
    except Exception:
        pass

    # Send order confirmation email
    try:
        adapters = get_adapters()
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT order_number, customer_name, contact_email, pickup_date, delivery_date, equipment_type, source_email_id FROM orders WHERE id = :id"),
                {"id": order_id},
            )
            order_data = result.mappings().first()

        if order_data and order_data.get("contact_email"):
            from order_shared.adapters.base import EmailMessage

            # Get the original email message_id for threading
            original_message_id = None
            if order_data.get("source_email_id"):
                async with async_session_factory() as session:
                    result = await session.execute(
                        text("SELECT message_id FROM emails WHERE id = :id"),
                        {"id": str(order_data["source_email_id"])},
                    )
                    row = result.fetchone()
                    if row:
                        original_message_id = row[0]

            customer_name = order_data.get("customer_name") or "Customer"
            order_number = order_data["order_number"]
            contact_email = order_data["contact_email"]
            pickup_date = str(order_data.get("pickup_date") or "TBD")
            delivery_date = str(order_data.get("delivery_date") or "TBD")
            equipment = order_data.get("equipment_type") or "N/A"

            email_msg = EmailMessage(
                to=contact_email,
                subject=f"Order Confirmed: {order_number}",
                body_html=f"<p>Dear {customer_name},</p><p>Your transportation order has been confirmed.</p><p><strong>Order Number:</strong> {order_number}<br><strong>Pickup Date:</strong> {pickup_date}<br><strong>Delivery Date:</strong> {delivery_date}<br><strong>Equipment:</strong> {equipment}</p><p>Best regards,<br>Order Processing Team</p>",
                body_text=f"Dear {customer_name},\n\nYour order has been confirmed.\n\nOrder Number: {order_number}\nPickup Date: {pickup_date}\nDelivery Date: {delivery_date}\nEquipment: {equipment}\n\nBest regards,\nOrder Processing Team",
                in_reply_to=original_message_id,
                references=[original_message_id] if original_message_id else [],
            )
            await adapters.email.send_email(email_msg)
    except Exception:
        pass  # Non-critical: email failure shouldn't block approval

    return {"message": "Order approved", "order_id": order_id, "status": "order_created"}


@router.post("/{order_id}/reject")
async def reject_order(
    order_id: str,
    body: ApproveRejectRequest | None = None,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Reject an order — moves it to 'cancelled'."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                UPDATE orders
                SET status = 'cancelled', reviewed_by_user_id = :user_id,
                    reviewed_at = NOW(), updated_at = NOW(),
                    internal_comments = COALESCE(:comments, internal_comments)
                WHERE id = :id AND status IN ('extracted', 'validated', 'pending_review')
                RETURNING id
            """),
            {
                "id": order_id,
                "user_id": current_user.id,
                "comments": body.comments if body else None,
            },
        )
        if not result.first():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INVALID_STATE",
                        "message": "Order not found or not in rejectable state",
                    }
                },
            )
        await session.commit()

        await session.execute(
            text("""
                INSERT INTO order_history (id, order_id, event_type, new_status, triggered_by, actor_id, created_at)
                VALUES (gen_random_uuid(), :order_id, 'order.rejected', 'cancelled', 'user', :actor_id, NOW())
            """),
            {"order_id": order_id, "actor_id": current_user.id},
        )
        await session.commit()

    return {"message": "Order rejected", "order_id": order_id, "status": "rejected"}


@router.post("/{order_id}/clone")
async def clone_order(
    order_id: str,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Clone an order — creates a copy with new ID and order_number."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}
        )
        source = result.mappings().first()
        if not source:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Order not found"}},
            )

        new_id = str(uuid.uuid4())
        new_order_number = f"ORD-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        await session.execute(
            text("""
                INSERT INTO orders (id, order_number, customer_id, customer_name,
                    pickup_address, pickup_date, delivery_address, delivery_date,
                    commodity, equipment_type, total_weight, weight_unit, notes,
                    status, processing_mode, contact_name, contact_email, contact_phone,
                    pickup_location_name, delivery_location_name, created_at)
                SELECT :new_id, :order_number, customer_id, customer_name,
                    pickup_address, pickup_date, delivery_address, delivery_date,
                    commodity, equipment_type, total_weight, weight_unit, notes,
                    'extracted', 'manual', contact_name, contact_email, contact_phone,
                    pickup_location_name, delivery_location_name, NOW()
                FROM orders WHERE id = :source_id
            """),
            {"new_id": new_id, "order_number": new_order_number, "source_id": order_id},
        )
        await session.commit()

        result = await session.execute(
            text("SELECT * FROM orders WHERE id = :id"), {"id": new_id}
        )
        new_order = dict(result.mappings().first())

    return _serialize_row(new_order)


@router.get("/{order_id}/history")
async def get_order_history(
    order_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    """Get order history/timeline."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                SELECT * FROM order_history
                WHERE order_id = :order_id
                ORDER BY created_at DESC
            """),
            {"order_id": order_id},
        )
        rows = [dict(r._mapping) for r in result]
    return {"data": _serialize_rows(rows)}


@router.get("/{order_id}/audit")
async def get_order_audit(
    order_id: str, current_user: CurrentUser = Depends(get_current_user)
):
    """Get audit log entries for an order."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                SELECT * FROM audit_logs
                WHERE entity_type = 'order' AND entity_id = :order_id
                ORDER BY timestamp DESC
            """),
            {"order_id": order_id},
        )
        rows = [dict(r._mapping) for r in result]
    return {"data": _serialize_rows(rows)}


# --- Helpers ---

import json


def _json_or_none(value: dict | None) -> str | None:
    if value is None:
        return None
    return json.dumps(value)


def _serialize_row(row: dict) -> dict:
    """Convert DB row to JSON-safe dict."""
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
