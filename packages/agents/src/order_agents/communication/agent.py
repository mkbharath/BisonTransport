"""Customer Communication Agent — generates and sends missing-info emails.

Uses LLM to fill email templates with missing field names,
sends via SMTP (MailHog locally), and tracks conversations.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from order_shared.adapters import get_adapters
from order_shared.adapters.base import EmailMessage, QueueMessage
from order_shared.db.session import async_session_factory
from order_shared.models.enums import AgentType
from order_agents.base_agent import BaseAgent


class CommunicationAgent(BaseAgent):
    """Sends automated missing-information emails to customers."""

    agent_type = AgentType.COMMUNICATION
    input_queue = "communication"

    async def process_message(self, message: QueueMessage) -> None:
        adapters = get_adapters()
        email_id = message.body["email_id"]
        order_id = message.body["order_id"]
        missing_fields = message.body.get("missing_fields", [])

        if not missing_fields:
            self.logger.info(f"No missing fields for order {order_id}, skipping communication")
            return

        # Load order and email details
        async with async_session_factory() as session:
            order_result = await session.execute(
                text("SELECT order_number, customer_name, contact_email FROM orders WHERE id = :id"),
                {"id": order_id},
            )
            order_row = order_result.fetchone()
            if not order_row:
                self.logger.error(f"Order {order_id} not found")
                return

            email_result = await session.execute(
                text("SELECT message_id, from_address FROM emails WHERE id = :id"),
                {"id": email_id},
            )
            email_row = email_result.fetchone()

        order_number, customer_name, contact_email = order_row
        original_message_id = email_row[0] if email_row else None
        customer_email_addr = contact_email or (email_row[1] if email_row else None)

        if not customer_email_addr:
            self.logger.warning(f"No customer email for order {order_id}, cannot send")
            return

        # Resolve human-readable field labels
        field_labels = await self._get_field_labels(missing_fields)

        # Generate email content using LLM
        email_body_html, email_body_text = await self._generate_email_content(
            customer_name=customer_name or "Customer",
            missing_field_labels=field_labels,
            order_reference=order_number,
        )

        # Send email
        email_msg = EmailMessage(
            to=customer_email_addr,
            subject=f"Action Required: Missing Information for Order {order_number}",
            body_html=email_body_html,
            body_text=email_body_text,
            in_reply_to=original_message_id,
            references=[original_message_id] if original_message_id else [],
        )

        sent_message_id = await adapters.email.send_email(email_msg)

        # Create/update conversation and log the outbound message
        conversation_id = uuid.uuid4()
        async with async_session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO conversations (id, order_id, thread_message_id, status, last_message_at, created_at)
                    VALUES (:id, :order_id, :thread_id, 'waiting', NOW(), NOW())
                    ON CONFLICT DO NOTHING
                """),
                {"id": str(conversation_id), "order_id": order_id, "thread_id": original_message_id},
            )
            await session.execute(
                text("""
                    INSERT INTO conversation_messages (id, conversation_id, direction, from_address, to_address, subject, body_html, body_text, sent_at, delivery_status)
                    VALUES (:id, :conv_id, 'outbound', :from_addr, :to_addr, :subject, :html, :text, NOW(), 'sent')
                """),
                {
                    "id": str(uuid.uuid4()),
                    "conv_id": str(conversation_id),
                    "from_addr": "orders@orderplatform.local",
                    "to_addr": customer_email_addr,
                    "subject": email_msg.subject,
                    "html": email_body_html,
                    "text": email_body_text,
                },
            )
            # Update order status
            await session.execute(
                text("UPDATE orders SET status = 'awaiting_customer', updated_at = NOW() WHERE id = :id"),
                {"id": order_id},
            )
            # Update email record with conversation link
            await session.execute(
                text("UPDATE emails SET conversation_id = :conv_id WHERE id = :id"),
                {"conv_id": str(conversation_id), "id": email_id},
            )
            # Log to order history
            await session.execute(
                text("""
                    INSERT INTO order_history (id, order_id, event_type, new_status, triggered_by, actor_id, detail_json, created_at)
                    VALUES (:id, :order_id, 'missing_info_sent', 'awaiting_customer', 'agent', :agent, :detail, NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "order_id": order_id,
                    "agent": self.agent_type,
                    "detail": json.dumps({"missing_fields": missing_fields, "sent_to": customer_email_addr}),
                },
            )
            await session.commit()

        self.logger.info(
            f"Missing-info email sent to {customer_email_addr} for order {order_number} "
            f"({len(field_labels)} missing fields)"
        )

    async def _get_field_labels(self, field_names: list[str]) -> list[str]:
        """Resolve field names to human-readable labels."""
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT field_name, label FROM field_configurations WHERE field_name = ANY(:names)"),
                {"names": field_names},
            )
            label_map = {row[0]: row[1] for row in result.fetchall()}

        return [label_map.get(f, f.replace("_", " ").title()) for f in field_names]

    async def _generate_email_content(
        self,
        customer_name: str,
        missing_field_labels: list[str],
        order_reference: str,
    ) -> tuple[str, str]:
        """Generate email content using LLM to fill template variables."""
        adapters = get_adapters()

        fields_list_html = "".join(f"<li>{label}</li>" for label in missing_field_labels)
        fields_list_text = "\n".join(f"- {label}" for label in missing_field_labels)

        # Use template structure with LLM-friendly variable substitution
        html_body = f"""<p>Dear {customer_name},</p>
<p>Thank you for your transportation order request. We are processing your order but require the following information to proceed:</p>
<ul>{fields_list_html}</ul>
<p>Please reply to this email with the missing details at your earliest convenience.</p>
<p><strong>Order Reference:</strong> {order_reference}</p>
<p>Please respond within 48 hours to avoid delays in processing.</p>
<p>Best regards,<br>Order Processing Team</p>"""

        text_body = f"""Dear {customer_name},

Thank you for your transportation order request. We require the following information:

{fields_list_text}

Please reply with the missing details.

Order Reference: {order_reference}
Please respond within 48 hours to avoid delays.

Best regards,
Order Processing Team"""

        return html_body, text_body
