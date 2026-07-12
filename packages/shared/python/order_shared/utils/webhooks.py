"""Webhook dispatcher — fires HTTP POST to configured endpoints on order events."""

import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from order_shared.db.session import async_session_factory

logger = logging.getLogger(__name__)


async def fire_webhooks(event_type: str, order_data: dict) -> None:
    """Fire all active webhooks matching the given event type.

    Args:
        event_type: e.g. "order_created", "order.approved", "order.rejected"
        order_data: dict with order_id, order_number, status, customer_name, etc.
    """
    try:
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT url, events, secret FROM webhooks WHERE active = true")
            )
            webhooks = result.mappings().fetchall()
    except Exception:
        # Table may not exist yet
        return

    if not webhooks:
        return

    payload = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": order_data,
    }
    payload_bytes = json.dumps(payload).encode()

    async with httpx.AsyncClient(timeout=10.0) as client:
        for wh in webhooks:
            # Check if this webhook subscribes to this event
            if event_type not in (wh["events"] or []):
                continue

            headers = {"Content-Type": "application/json"}

            # Add HMAC signature if secret is set
            if wh.get("secret"):
                signature = hmac.new(
                    wh["secret"].encode(), payload_bytes, hashlib.sha256
                ).hexdigest()
                headers["X-Webhook-Signature"] = f"sha256={signature}"

            try:
                response = await client.post(wh["url"], content=payload_bytes, headers=headers)
                logger.info(f"Webhook fired: {wh['url']} event={event_type} status={response.status_code}")
            except Exception as e:
                logger.warning(f"Webhook failed: {wh['url']} event={event_type} error={e}")
