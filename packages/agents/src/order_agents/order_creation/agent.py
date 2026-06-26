"""Order Creation Agent — finalizes orders and sends acknowledgements.

Consumes from auto-process queue (high confidence orders) or triggered
by HITL approval. Sends acknowledgement email to customer.
"""

import json
import uuid
from typing import Any

from sqlalchemy import text

from order_shared.adapters import get_adapters
from order_shared.adapters.base import EmailMessage, Event, QueueMessage
from order_shared.db.session import async_session_factory
from order_shared.models.enums import AgentType
from order_agents.base_agent import BaseAgent


class OrderCreationAgent(BaseAgent):
    """Creates orders after validation pass or HITL approval."""

    agent_type = AgentType.ORDER_CREATION
    input_queue = "auto-process"

    async def process_message(self, message: QueueMessage) -> None:
        adapters = get_adapters()
        order_id = message.body["order_id"]
        email_id = message.body.get("email_id")

        # Load order
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}
            )
            order = result.mappings().fetchone()
            if not order:
                self.logger.error(f"Order {order_id} not found")
                return

        # Idempotency check — don't re-create
        if order["status"] == "order_created":
            self.logger.info(f"Order {order_id} already created, skipping")
            return

        # Update order status to order_created
        async with async_session_factory() as session:
            await session.execute(
                text("""
                    UPDATE orders SET status = 'order_created', processing_mode = :mode, updated_at = NOW()
                    WHERE id = :id
                """),
                {"id": order_id, "mode": order.get("processing_mode", "auto")},
            )
            # Log to order history
            await session.execute(
                text("""
                    INSERT INTO order_history (id, order_id, event_type, previous_status, new_status, triggered_by, actor_id, detail_json, created_at)
                    VALUES (:id, :order_id, 'order_created', :prev_status, 'order_created', 'agent', :agent, :detail, NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "order_id": order_id,
                    "prev_status": order["status"],
                    "agent": self.agent_type,
                    "detail": json.dumps({"confidence": float(order.get("overall_confidence_score") or 0)}),
                },
            )
            await session.commit()

        # Send acknowledgement email
        contact_email = order.get("contact_email")
        if contact_email:
            await self._send_acknowledgement(order)

        # Publish order.created event
        await adapters.events.publish_event(Event(
            source="order-creation-agent",
            detail_type="order.created",
            detail={
                "order_id": order_id,
                "order_number": order["order_number"],
                "customer_name": order.get("customer_name"),
                "processing_mode": order.get("processing_mode", "auto"),
            },
        ))

        self.logger.info(
            f"Order {order['order_number']} created successfully "
            f"(mode={order.get('processing_mode', 'auto')})"
        )

    async def _send_acknowledgement(self, order: Any) -> None:
        """Send order acknowledgement email as a reply in the same thread."""
        adapters = get_adapters()

        customer_name = order.get("customer_name", "Customer")
        order_number = order["order_number"]
        contact_email = order["contact_email"]
        pickup_date = str(order.get("pickup_date", "TBD"))
        delivery_date = str(order.get("delivery_date", "TBD"))
        equipment = order.get("equipment_type", "N/A")

        # Get the original email's message_id for threading
        # Use the MOST RECENT email linked to this order (customer's latest reply)
        original_message_id = None
        source_email_id = order.get("source_email_id")
        if source_email_id:
            async with async_session_factory() as session:
                from sqlalchemy import text as sa_text
                # Find the latest email in the thread for this order
                result = await session.execute(
                    sa_text("""
                        SELECT message_id FROM emails
                        WHERE linked_order_id = :order_id
                        ORDER BY created_at DESC
                        LIMIT 1
                    """),
                    {"order_id": str(order.get("id"))},
                )
                row = result.fetchone()
                if row:
                    original_message_id = row[0]
                else:
                    # Fallback to source email
                    result = await session.execute(
                        sa_text("SELECT message_id FROM emails WHERE id = :id"),
                        {"id": str(source_email_id)},
                    )
                    row = result.fetchone()
                    if row:
                        original_message_id = row[0]

        html_body = f"""<p>Dear {customer_name},</p>
<p>Your transportation order has been successfully created.</p>
<p><strong>Order Number:</strong> {order_number}<br>
<strong>Pickup Date:</strong> {pickup_date}<br>
<strong>Delivery Date:</strong> {delivery_date}<br>
<strong>Equipment:</strong> {equipment}</p>
<p>You will receive updates as your shipment progresses.</p>
<p>Best regards,<br>Order Processing Team</p>"""

        text_body = f"""Dear {customer_name},

Your order has been confirmed.

Order Number: {order_number}
Pickup Date: {pickup_date}
Delivery Date: {delivery_date}
Equipment: {equipment}

Best regards,
Order Processing Team"""

        email_msg = EmailMessage(
            to=contact_email,
            subject=f"Order Confirmed: {order_number}",
            body_html=html_body,
            body_text=text_body,
            in_reply_to=original_message_id,
            references=[original_message_id] if original_message_id else [],
        )

        try:
            await adapters.email.send_email(email_msg)
            self.logger.info(f"Acknowledgement email sent to {contact_email} (in thread)")
        except Exception as e:
            self.logger.warning(f"Failed to send acknowledgement: {e}")
