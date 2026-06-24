"""Conversation management endpoints."""

import math
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text

from order_shared.db.session import async_session_factory

from order_api.auth import CurrentUser, get_current_user, require_role

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


class ReplyRequest(BaseModel):
    body_text: str
    body_html: str | None = None
    subject: str | None = None


@router.get("")
async def list_conversations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    """List conversations with pagination."""
    offset = (page - 1) * limit
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if status:
        conditions.append("c.status = :status")
        params["status"] = status

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    async with async_session_factory() as session:
        count_result = await session.execute(
            text(f"SELECT COUNT(*) FROM conversations c WHERE {where_clause}"), params
        )
        total_count = count_result.scalar() or 0

        result = await session.execute(
            text(f"""
                SELECT c.* FROM conversations c
                WHERE {where_clause}
                ORDER BY c.last_message_at DESC NULLS LAST
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


@router.get("/{conversation_id}")
async def get_conversation_thread(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get conversation with full message thread."""
    async with async_session_factory() as session:
        result = await session.execute(
            text("SELECT * FROM conversations WHERE id = :id"),
            {"id": conversation_id},
        )
        conversation = result.mappings().first()
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Conversation not found"}},
            )

        messages_result = await session.execute(
            text("""
                SELECT * FROM conversation_messages
                WHERE conversation_id = :cid
                ORDER BY sent_at ASC NULLS LAST
            """),
            {"cid": conversation_id},
        )
        messages = [dict(r._mapping) for r in messages_result]

    conv_data = _serialize_row(dict(conversation))
    conv_data["messages"] = _serialize_rows(messages)
    return conv_data


@router.post("/{conversation_id}/reply")
async def reply_to_conversation(
    conversation_id: str,
    body: ReplyRequest,
    current_user: CurrentUser = Depends(require_role("agent")),
):
    """Add a reply to a conversation."""
    async with async_session_factory() as session:
        # Verify conversation exists
        result = await session.execute(
            text("SELECT * FROM conversations WHERE id = :id"),
            {"id": conversation_id},
        )
        conversation = result.mappings().first()
        if not conversation:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "NOT_FOUND", "message": "Conversation not found"}},
            )

        msg_id = str(uuid.uuid4())
        await session.execute(
            text("""
                INSERT INTO conversation_messages
                    (id, conversation_id, direction, from_address, subject, body_text, body_html, sent_at, delivery_status)
                VALUES
                    (:id, :cid, 'outbound', :from_addr, :subject, :body_text, :body_html, NOW(), 'sent')
            """),
            {
                "id": msg_id,
                "cid": conversation_id,
                "from_addr": current_user.email,
                "subject": body.subject,
                "body_text": body.body_text,
                "body_html": body.body_html,
            },
        )

        # Update conversation
        await session.execute(
            text("UPDATE conversations SET last_message_at = NOW(), status = 'active' WHERE id = :id"),
            {"id": conversation_id},
        )
        await session.commit()

    return {"message": "Reply sent", "message_id": msg_id}


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
