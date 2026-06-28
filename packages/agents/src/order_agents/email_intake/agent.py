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
- new_order: Customer is submitting a brand new transportation/shipping order with full details (addresses, dates, commodity, weight, equipment)
- order_update: Customer is proactively changing details on an existing order (e.g., "please change delivery date to..." or "update the weight to...")
- customer_response: Customer is REPLYING to a previous email from us. Key indicators: subject starts with "Re:" or "RE:", references an order number (ORD-...), mentions "here is the information" or "as requested" or provides specific fields that were asked for. If the subject contains "Action Required" or "Missing Information" it is definitely a customer_response.
- cancellation: Customer explicitly wants to cancel an order
- other: Not related to orders (spam, newsletters, internal communications, general inquiries without order details)

IMPORTANT: If the subject line contains "Re:" AND references "Action Required" or "Missing Information" or an order number like "ORD-XXXXXXXX-XXXXX", classify as customer_response, NOT order_update.

IMPORTANT: If the email has file attachments (PDF, Excel, Word) and the body mentions "attached", "shipment", "order", "rate confirmation", or "please process", classify as new_order — the order details are in the attachment.

Respond with JSON: {"category": "<category>", "confidence": <0-100>}"""


class EmailIntakeAgent:
    """Email Intake Agent supporting multiple modes:

    - file_watcher: watches a directory for .eml files (local dev)
    - msgraph: polls Microsoft 365 mailbox via Graph API (production)
    """

    agent_type = AgentType.EMAIL_INTAKE

    def __init__(self) -> None:
        self.logger = get_logger("agent.email_intake")
        self._running = False
        self._inbox_dir = Path(os.environ.get("EMAIL_INBOX_DIR", "./test-emails/inbox"))
        self._processed_files: set[str] = set()
        self._poll_interval = int(os.environ.get("EMAIL_POLL_INTERVAL_SECONDS", "5"))
        self._intake_mode = os.environ.get("EMAIL_INTAKE_MODE", "file_watcher")
        self._msgraph_poller = None

    async def run(self) -> None:
        """Main loop: delegates to the configured intake mode."""
        self._running = True

        if self._intake_mode == "msgraph":
            await self._run_msgraph_mode()
        else:
            await self._run_file_watcher_mode()

    async def _run_file_watcher_mode(self) -> None:
        """Watch inbox directory for new .eml files."""
        self._inbox_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Email Intake Agent started in FILE WATCHER mode, watching {self._inbox_dir}")

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

    async def _run_msgraph_mode(self) -> None:
        """Poll Microsoft 365 mailbox via Graph API."""
        from order_agents.email_intake.msgraph_poller import MSGraphEmailPoller

        tenant_id = os.environ.get("MSGRAPH_TENANT_ID", "")
        client_id = os.environ.get("MSGRAPH_CLIENT_ID", "")
        client_secret = os.environ.get("MSGRAPH_CLIENT_SECRET", "")
        mailbox = os.environ.get("MSGRAPH_MAILBOX", "iltransport@ideyalabs.com")

        if not all([tenant_id, client_id, client_secret]):
            self.logger.error(
                "MS Graph credentials not configured. Set MSGRAPH_TENANT_ID, "
                "MSGRAPH_CLIENT_ID, MSGRAPH_CLIENT_SECRET in .env.local"
            )
            return

        self._msgraph_poller = MSGraphEmailPoller(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
            mailbox=mailbox,
        )

        self.logger.info(f"Email Intake Agent started in MS GRAPH mode, polling {mailbox}")

        while self._running:
            try:
                emails = await self._msgraph_poller.get_unread_emails(max_count=10)
                for graph_msg in emails:
                    await self._process_graph_email(graph_msg)
            except Exception as e:
                self.logger.error(f"Error polling MS Graph: {e}", exc_info=True)

            await asyncio.sleep(self._poll_interval)

    async def _process_graph_email(self, graph_msg: dict) -> None:
        """Process a single email from Microsoft Graph API."""
        run_id = uuid.uuid4()
        set_log_context(run_id=run_id, agent_type=self.agent_type)

        try:
            # Parse to our internal format
            email_record = self._msgraph_poller.parse_email_record(graph_msg)
            message_id = email_record["message_id"]
            self.logger.info(f"Processing email from MS Graph: {email_record['subject']}")

            # Check for duplicate Message-ID
            email_id = uuid.uuid4()
            async with async_session_factory() as session:
                result = await session.execute(
                    text("SELECT id FROM emails WHERE message_id = :mid"),
                    {"mid": message_id},
                )
                if result.scalar():
                    self.logger.info(f"Duplicate Message-ID, skipping: {message_id}")
                    # Still mark as read to avoid re-polling
                    await self._msgraph_poller.mark_as_read(graph_msg["id"])
                    return

                # Classify the email using LLM
                adapters = get_adapters()
                body_text = email_record["body_text"] or _strip_html(email_record["body_html"]) or ""
                snippet = body_text[:500]

                # Add attachment context to help classification
                has_attachments = email_record.get("has_attachments", False)
                attachment_hint = ""
                if has_attachments:
                    attachment_hint = "\nNote: This email has file attachments (likely PDF/Excel with order details)."

                classification_input = (
                    f"Subject: {email_record['subject']}\n"
                    f"From: {email_record['from_address']}\n"
                    f"Body:\n{snippet}"
                    f"{attachment_hint}"
                )

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
                        "thread_id": email_record["thread_id"],
                        "from_address": email_record["from_address"],
                        "to_address": email_record["to_address"],
                        "subject": email_record["subject"],
                        "body_text": email_record["body_text"] or _strip_html(email_record["body_html"]),
                        "body_html": email_record["body_html"],
                        "received_at": datetime.fromisoformat(email_record["received_at"].replace("Z", "+00:00")) if email_record["received_at"] else datetime.now(timezone.utc),
                        "classification": classification,
                        "confidence": confidence,
                    },
                )
                await session.commit()

            # Process attachments from Graph API
            attachment_ids = []
            if email_record["has_attachments"]:
                attachment_ids = await self._process_graph_attachments(
                    graph_msg["id"], email_id
                )

            self.logger.info(
                f"Email classified as '{classification}' ({confidence:.1f}%), "
                f"{len(attachment_ids)} attachments"
            )

            # Mark as read in mailbox
            await self._msgraph_poller.mark_as_read(graph_msg["id"])

            # Route based on classification
            # Both customer_response AND order_update should try to match existing orders
            if classification in ("customer_response", "order_update"):
                original_order = await self._find_related_order(
                    email_record["from_address"],
                    email_record["thread_id"],
                    email_record["subject"],
                    email_id,
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
                        f"Reply linked to order {original_order['order_number']}"
                    )
                else:
                    # No matching order — treat as new
                    await adapters.queue.publish_message(
                        queue_name="document-processing",
                        body={
                            "email_id": str(email_id),
                            "classification": classification,
                            "attachment_ids": attachment_ids,
                        },
                    )
                    self.logger.info(f"No matching order found, treating as new")
            elif classification == "new_order":
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
                async with async_session_factory() as session:
                    await session.execute(
                        text("UPDATE emails SET status = 'processed' WHERE id = :id"),
                        {"id": str(email_id)},
                    )
                    await session.commit()

        except Exception as e:
            self.logger.error(f"Failed to process Graph email: {e}", exc_info=True)
        finally:
            clear_log_context()

    async def _process_graph_attachments(
        self, graph_message_id: str, email_id: uuid.UUID
    ) -> list[str]:
        """Download and store attachments from MS Graph."""
        adapters = get_adapters()
        attachment_ids: list[str] = []

        attachments = await self._msgraph_poller.get_attachments(graph_message_id)

        for att in attachments:
            filename = att["name"]
            file_data = att["content_bytes"]
            content_type = att["content_type"]
            file_type = filename.rsplit(".", 1)[-1].lower() if "." in filename else "unknown"

            # Size check (25 MB)
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
                snippet = (body_text or _strip_html(body_html) or "")[:500]
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
        1. Match by order number in subject line (e.g., "Re: ... ORD-20260625-00051")
        2. Match by thread_id (In-Reply-To/conversationId)
        3. Match by contact_email on order + 'awaiting_customer' status
        4. Match by sender email + 'awaiting_customer' status
        """
        import re

        async with async_session_factory() as session:
            # Strategy 1: Extract order number from subject line
            if subject:
                order_match = re.search(r"ORD-\d{8}-\d{5}", subject)
                if order_match:
                    order_number = order_match.group(0)
                    result = await session.execute(
                        text("""
                            SELECT id, order_number, status FROM orders
                            WHERE order_number = :order_number
                            AND status = 'awaiting_customer'
                            LIMIT 1
                        """),
                        {"order_number": order_number},
                    )
                    row = result.mappings().first()
                    if row:
                        return dict(row)

            # Strategy 2: Match by thread/conversation
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

            # Strategy 4: Match by sender email domain + awaiting_customer status
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


def _strip_html(html: str | None) -> str:
    """Strip HTML tags and extract readable text content."""
    if not html:
        return ""
    import re
    # Remove style and script blocks
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Replace br and p tags with newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)
    # Remove all remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = text.replace("&nbsp;", " ").replace("&quot;", '"')
    # Clean up whitespace
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()
