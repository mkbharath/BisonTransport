"""Email Intake Agent — file watcher mode for local development.

Monitors a directory for new .eml files, parses them, classifies using LLM,
stores attachments in MinIO, persists email records, and publishes to
document-processing queue.
"""

import asyncio
import email
import os
import uuid
from datetime import datetime, timezone
from email import policy
from pathlib import Path
from typing import Any

from sqlalchemy import text

from order_shared.adapters import get_adapters
from order_shared.adapters.base import QueueMessage
from order_shared.db.session import async_session_factory
from order_shared.models.enums import AgentType, EmailClassification
from order_shared.utils.logger import get_logger, set_log_context, clear_log_context

logger = get_logger(__name__)

CLASSIFICATION_SYSTEM_PROMPT = """You are an email classifier for a transportation and logistics company.
Classify the incoming email into exactly one category based on its subject, sender, and body content.

Categories:
- new_order: Customer is submitting a new transportation/shipping order
- order_update: Customer is updating an existing order (changes to dates, addresses, etc.)
- customer_response: Customer is replying to a previous request for information
- cancellation: Customer wants to cancel an order
- other: Not related to orders (spam, newsletters, internal communications, etc.)

Respond with JSON: {"category": "<category>", "confidence": <0-100>}"""


class EmailIntakeAgent:
    """Email Intake Agent using file watcher mode for local development.

    In local mode, watches a directory for .eml files instead of polling IMAP.
    """

    agent_type = AgentType.EMAIL_INTAKE

    def __init__(self) -> None:
        self.logger = get_logger("agent.email_intake")
        self._running = False
        self._inbox_dir = Path(os.environ.get("EMAIL_INBOX_DIR", "./test-emails/inbox"))
        self._processed_files: set[str] = set()
        self._poll_interval = int(os.environ.get("EMAIL_POLL_INTERVAL_SECONDS", "5"))

    async def run(self) -> None:
        """Main loop: watch inbox directory for new .eml files."""
        self._running = True
        self._inbox_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Email Intake Agent started, watching {self._inbox_dir}")

        while self._running:
            try:
                eml_files = list(self._inbox_dir.glob("*.eml"))
                for eml_path in eml_files:
                    if str(eml_path) not in self._processed_files:
                        await self._process_eml_file(eml_path)
                        self._processed_files.add(str(eml_path))
            except Exception as e:
                self.logger.error(f"Error scanning inbox: {e}", exc_info=True)

            await asyncio.sleep(self._poll_interval)

    async def _process_eml_file(self, eml_path: Path) -> None:
        """Parse and process a single .eml file."""
        run_id = uuid.uuid4()
        set_log_context(run_id=run_id, agent_type=self.agent_type)

        try:
            self.logger.info(f"Processing email file: {eml_path.name}")

            # Parse the .eml file
            with open(eml_path, "rb") as f:
                msg = email.message_from_bytes(f.read(), policy=policy.default)

            # Extract metadata
            message_id = msg.get("Message-ID", f"<local-{uuid.uuid4()}@local>")
            thread_id = msg.get("In-Reply-To") or msg.get("References", "").split()[0] if msg.get("References") else None
            from_address = msg.get("From", "unknown@unknown.com")
            to_address = msg.get("To", "orders@orderplatform.local")
            subject = msg.get("Subject", "")
            date_str = msg.get("Date")
            received_at = datetime.now(timezone.utc)

            # Extract body
            body_text = ""
            body_html = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain" and not body_text:
                        body_text = part.get_content()
                    elif content_type == "text/html" and not body_html:
                        body_html = part.get_content()
            else:
                content_type = msg.get_content_type()
                if content_type == "text/plain":
                    body_text = msg.get_content()
                elif content_type == "text/html":
                    body_html = msg.get_content()

            # Check for duplicate Message-ID
            email_id = uuid.uuid4()
            async with async_session_factory() as session:
                result = await session.execute(
                    text("SELECT id FROM emails WHERE message_id = :mid"),
                    {"mid": message_id},
                )
                if result.scalar():
                    self.logger.info(f"Duplicate Message-ID, skipping: {message_id}")
                    return

                # Classify the email using LLM
                adapters = get_adapters()
                snippet = (body_text or body_html or "")[:500]
                classification_input = f"Subject: {subject}\nFrom: {from_address}\nBody:\n{snippet}"

                classification, confidence = await adapters.llm.classify(
                    text=classification_input,
                    categories=[e.value for e in EmailClassification],
                    system=CLASSIFICATION_SYSTEM_PROMPT,
                )

                # Persist email record
                await session.execute(
                    text("""
                        INSERT INTO emails (id, message_id, thread_id, from_address, to_address,
                            subject, body_text, body_html, received_at, processed_at,
                            classification, classification_confidence, status, created_at)
                        VALUES (:id, :message_id, :thread_id, :from_address, :to_address,
                            :subject, :body_text, :body_html, :received_at, NOW(),
                            :classification, :confidence, 'processing', NOW())
                    """),
                    {
                        "id": str(email_id),
                        "message_id": message_id,
                        "thread_id": thread_id,
                        "from_address": from_address,
                        "to_address": to_address,
                        "subject": subject,
                        "body_text": body_text,
                        "body_html": body_html,
                        "received_at": received_at,
                        "classification": classification,
                        "confidence": confidence,
                    },
                )
                await session.commit()

            # Process attachments
            attachment_ids = await self._process_attachments(msg, email_id)

            self.logger.info(
                f"Email classified as '{classification}' ({confidence:.1f}%), "
                f"{len(attachment_ids)} attachments"
            )

            # Only route new_order, order_update, and customer_response to pipeline
            if classification == "customer_response":
                # Find the original order this is replying to
                original_order = await self._find_related_order(
                    from_address, thread_id, subject, email_id
                )
                if original_order:
                    await adapters.queue.publish_message(
                        queue_name="document-processing",
                        body={
                            "email_id": str(email_id),
                            "classification": classification,
                            "attachment_ids": attachment_ids,
                            "related_order_id": str(original_order["id"]),
                            "is_customer_response": True,
                        },
                    )
                    self.logger.info(
                        f"Customer response linked to order {original_order['order_number']}, "
                        f"published for re-processing"
                    )
                else:
                    # No matching order found — treat as new order
                    await adapters.queue.publish_message(
                        queue_name="document-processing",
                        body={
                            "email_id": str(email_id),
                            "classification": classification,
                            "attachment_ids": attachment_ids,
                        },
                    )
                    self.logger.info(f"Customer response with no matching order, treating as new")
            elif classification in ("new_order", "order_update"):
                await adapters.queue.publish_message(
                    queue_name="document-processing",
                    body={
                        "email_id": str(email_id),
                        "classification": classification,
                        "attachment_ids": attachment_ids,
                    },
                )
                self.logger.info(f"Published to document-processing queue")
            else:
                # Mark as processed but don't route
                async with async_session_factory() as session:
                    await session.execute(
                        text("UPDATE emails SET status = 'processed' WHERE id = :id"),
                        {"id": str(email_id)},
                    )
                    await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to process {eml_path.name}: {e}", exc_info=True)
        finally:
            clear_log_context()

    async def _find_related_order(
        self, from_address: str, thread_id: str | None, subject: str | None, email_id: uuid.UUID
    ) -> dict | None:
        """Find the original order that this customer response relates to.

        Matching strategy (in priority order):
        1. Match by thread_id (In-Reply-To header matches an outbound conversation message)
        2. Match by customer email + 'awaiting_customer' status (most recent)
        """
        async with async_session_factory() as session:
            # Strategy 1: Match by thread/conversation
            if thread_id:
                result = await session.execute(
                    text("""
                        SELECT o.id, o.order_number, o.status FROM orders o
                        JOIN conversations c ON c.order_id = o.id
                        WHERE c.thread_message_id = :thread_id
                        AND o.status = 'awaiting_customer'
                        LIMIT 1
                    """),
                    {"thread_id": thread_id},
                )
                row = result.mappings().first()
                if row:
                    return dict(row)

            # Strategy 2: Match by sender email domain + awaiting_customer status
            # Find orders linked to emails from the same sender that are awaiting response
            sender_domain = from_address.split("@")[-1] if "@" in from_address else ""
            if sender_domain:
                result = await session.execute(
                    text("""
                        SELECT o.id, o.order_number, o.status FROM orders o
                        JOIN emails e ON e.linked_order_id = o.id
                        WHERE e.from_address LIKE :domain_pattern
                        AND o.status = 'awaiting_customer'
                        ORDER BY o.created_at DESC
                        LIMIT 1
                    """),
                    {"domain_pattern": f"%@{sender_domain}"},
                )
                row = result.mappings().first()
                if row:
                    return dict(row)

            # Strategy 3: Match by contact_email on order
            result = await session.execute(
                text("""
                    SELECT id, order_number, status FROM orders
                    WHERE contact_email = :email
                    AND status = 'awaiting_customer'
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"email": from_address},
            )
            row = result.mappings().first()
            if row:
                return dict(row)

        return None

    async def _process_attachments(
        self, msg: Any, email_id: uuid.UUID
    ) -> list[str]:
        """Download and store all attachments from the email."""
        adapters = get_adapters()
        attachment_ids: list[str] = []

        if not msg.is_multipart():
            return attachment_ids

        for part in msg.walk():
            content_disposition = part.get("Content-Disposition", "")
            if "attachment" not in content_disposition and part.get_filename() is None:
                continue

            filename = part.get_filename()
            if not filename:
                continue

            # Get file content
            file_data = part.get_payload(decode=True)
            if not file_data:
                continue

            content_type = part.get_content_type()
            file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"

            # Check size limit (25 MB)
            if len(file_data) > 25 * 1024 * 1024:
                self.logger.warning(f"Attachment {filename} exceeds 25MB, skipping")
                continue

            # Upload to storage
            now = datetime.now(timezone.utc)
            s3_key = f"attachments/{now.year}/{now.month:02d}/{email_id}/{filename}"

            await adapters.storage.upload_file(
                bucket="attachments",
                key=s3_key,
                data=file_data,
                content_type=content_type,
            )

            # Persist attachment record
            att_id = uuid.uuid4()
            async with async_session_factory() as session:
                await session.execute(
                    text("""
                        INSERT INTO email_attachments
                        (id, email_id, file_name, file_type, file_size_bytes, s3_key, processing_status, created_at)
                        VALUES (:id, :email_id, :filename, :file_type, :size, :s3_key, 'pending', NOW())
                    """),
                    {
                        "id": str(att_id),
                        "email_id": str(email_id),
                        "filename": filename,
                        "file_type": file_type,
                        "size": len(file_data),
                        "s3_key": s3_key,
                    },
                )
                await session.commit()

            attachment_ids.append(str(att_id))
            self.logger.info(f"Stored attachment: {filename} ({len(file_data)} bytes)")

        return attachment_ids

    def stop(self) -> None:
        self._running = False
