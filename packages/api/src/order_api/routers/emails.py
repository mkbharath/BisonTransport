"""Email management endpoints."""

import math
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text

from order_shared.adapters import get_adapters
from order_shared.db.session import async_session_factory

from order_api.auth import CurrentUser, get_current_user, require_role

router = APIRouter(prefix="/api/v1/emails", tags=["emails"])


@router.get("")
async def list_emails(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    classification: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List emails with pagination and optional filters."""
    offset = (page - 1) * limit
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if status:
        conditions.append("e.status = :status")
        params["status"] = status
    if classification:
        conditions.append("e.classification = :classification")
        params["classification"] = classification

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    async with async_session_factory() as session:
        count_result = await session.execute(
            text(f"SELECT COUNT(*) FROM emails e WHERE {where_clause}"), params
        )
        total_count = count_result.scalar() or 0

        result = await session.execute(
            text(f"""
                SELECT e.* FROM emails e
                WHERE {where_clause}
                ORDER BY e.received_at DESC
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


@router.get("/{email_id}")
async def get_email(email_id: str, current_user: CurrentUser = Depends(get_current_user)):
    """Get email detail including attachments."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM emails WHERE id = :id"), {"id": email_id}
        )
        email = result.mappings().first()
        if not email:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Email not found"}},
            )

        att_result = await session.execute(
            text("SELECT * FROM email_attachments WHERE email_id = :email_id"),
            {"email_id": email_id},
        )
        attachments = [dict(r._mapping) for r in att_result]

    email_data = _serialize_row(dict(email))
    email_data["attachments"] = _serialize_rows(attachments)
    return email_data


@router.post("/{email_id}/reclassify")
async def reclassify_email(
    email_id: str,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Trigger reclassification of an email."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT id FROM emails WHERE id = :id"), {"id": email_id}
        )
        if not result.first():
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Email not found"}},
            )

        await session.execute(
            text("""
                UPDATE emails SET status = 'pending_reclassification', updated_at = NOW()
                WHERE id = :id
            """),
            {"id": email_id},
        )
        await session.commit()

    return {"message": "Email queued for reclassification", "email_id": email_id}


@router.get("/{email_id}/attachments/{attachment_id}/url")
async def get_attachment_url(
    email_id: str,
    attachment_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a presigned URL for downloading an attachment."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("""
                SELECT * FROM email_attachments
                WHERE id = :att_id AND email_id = :email_id
            """),
            {"att_id": attachment_id, "email_id": email_id},
        )
        attachment = result.mappings().first()
        if not attachment:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Attachment not found"}},
            )

    bucket = os.environ.get("STORAGE_BUCKET_ATTACHMENTS", "attachments")
    adapters = get_adapters()
    url = await adapters.storage.get_presigned_url(bucket, attachment["s3_key"], expires_in=900)

    return {"url": url, "file_name": attachment["file_name"], "expires_in": 900}


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
