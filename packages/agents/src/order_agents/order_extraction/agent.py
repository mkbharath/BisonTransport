"""Order Extraction Agent — LLM-based structured data extraction.

Takes combined text from email body + attachments, calls Claude to extract
all order fields with per-field confidence scores.
"""

import json
import uuid
from typing import Any

from sqlalchemy import text

from order_shared.adapters import get_adapters
from order_shared.adapters.base import QueueMessage
from order_shared.db.session import async_session_factory
from order_shared.models.enums import AgentType, OrderStatus
from order_shared.models.order import OrderSchema
from order_shared.utils.normalizers import (
    expand_address_abbreviations,
    normalize_date,
    normalize_phone,
    normalize_weight,
)
from order_agents.base_agent import BaseAgent

EXTRACTION_SYSTEM_PROMPT = """You are an expert data extraction agent for a transportation and logistics company.
Extract ALL order fields from the provided text. The text may come from email body, PDF documents, Excel spreadsheets, or scanned images.

Return a JSON object with two top-level keys:
1. "order": containing all extracted fields
2. "confidence_scores": containing a confidence score (0-100) for each field

Order fields to extract:
- customer_name, contact_name, contact_email, contact_phone
- pickup_location_name, pickup_address_line1, pickup_city, pickup_state, pickup_postal_code, pickup_country, pickup_date, pickup_time_start, pickup_time_end, pickup_instructions
- delivery_location_name, delivery_address_line1, delivery_city, delivery_state, delivery_postal_code, delivery_country, delivery_date, delivery_time_start, delivery_time_end, delivery_instructions
- customer_order_number, reference_number, po_number
- commodity, freight_type (ftl|ltl|partial|intermodal), total_weight, weight_unit (lbs|kgs), dimensions, total_quantity, num_pallets, stackable
- equipment_type (dry_van|flatbed|reefer|step_deck|tanker|lowboy|conestoga|other), truck_size, temperature_min_c, temperature_max_c
- hazmat_indicator (true|false), hazmat_un_number, hazmat_class
- special_handling_instructions, liftgate_required, team_drive_required, twic_card_required
- notes

Rules:
- Set fields to null if not found in the text
- For confidence_scores, use 0 for fields not found, and 60-100 for fields found (higher = more certain)
- Normalize dates to YYYY-MM-DD format
- Normalize weight units: pounds/lbs -> "lbs", kilograms/kgs/kg -> "kgs"
- For boolean fields, use true/false
- Return ONLY valid JSON, no other text"""


class OrderExtractionAgent(BaseAgent):
    """Extracts structured order data from combined document text using LLM."""

    agent_type = AgentType.ORDER_EXTRACTION
    input_queue = "extraction"

    async def process_message(self, message: QueueMessage) -> None:
        """Extract order fields from combined text corpus."""
        adapters = get_adapters()
        email_id = message.body["email_id"]
        email_body = message.body.get("email_body", "")
        extraction_results = message.body.get("extraction_results", [])
        is_customer_response = message.body.get("is_customer_response", False)
        related_order_id = message.body.get("related_order_id")

        # If this is a customer response, handle as merge into existing order
        if is_customer_response and related_order_id:
            await self._process_customer_response(
                email_id, email_body, extraction_results, related_order_id
            )
            return

        # Combine all text sources
        text_parts = []
        if email_body:
            text_parts.append(f"--- EMAIL BODY ---\n{email_body}")
        for ext in extraction_results:
            if ext.get("text"):
                text_parts.append(
                    f"--- ATTACHMENT: {ext.get('file_name', 'unknown')} ---\n{ext['text']}"
                )
            # Include table data as text
            for table in ext.get("tables", []):
                if table.get("rows"):
                    text_parts.append(
                        f"--- TABLE from {ext.get('file_name', 'unknown')} ---\n"
                        + json.dumps(table["rows"][:20], indent=2)  # Limit rows for token budget
                    )

        combined_text = "\n\n".join(text_parts)

        if not combined_text.strip():
            self.logger.warning(f"No text content for email {email_id}, skipping extraction")
            return

        # Truncate to ~50k tokens (~200k chars) if needed
        if len(combined_text) > 200000:
            combined_text = combined_text[:200000]
            self.logger.info("Truncated combined text to 200k chars for token budget")

        # Call LLM for extraction (with retry on malformed JSON)
        extracted_data = await self._call_llm_with_retry(combined_text)

        if not extracted_data:
            self.logger.error(f"LLM extraction failed for email {email_id}")
            return

        # Normalize extracted values
        order_data = extracted_data.get("order", {})
        confidence_scores = extracted_data.get("confidence_scores", {})

        normalized = self._normalize_fields(order_data)

        # Compute overall confidence
        from order_shared.utils.confidence import compute_weighted_confidence

        mandatory_fields = [
            "customer_name", "contact_name", "contact_email",
            "pickup_location_name", "pickup_date",
            "delivery_location_name", "delivery_date",
            "commodity", "freight_type", "total_weight", "weight_unit",
            "equipment_type", "hazmat_indicator",
        ]
        overall_confidence = compute_weighted_confidence(confidence_scores, mandatory_fields)

        # Persist order to DB
        order_id = uuid.uuid4()
        order_number = await self._generate_order_number()

        async with async_session_factory() as session:
            await session.execute(
                text("""
                    INSERT INTO orders (id, order_number, source_email_id, status,
                        overall_confidence_score, processing_mode, field_confidence_scores,
                        customer_name, contact_name, contact_email, contact_phone,
                        pickup_location_name, pickup_address, pickup_date, pickup_instructions,
                        delivery_location_name, delivery_address, delivery_date, delivery_instructions,
                        customer_order_number, reference_number, po_number,
                        commodity, freight_type, total_weight, weight_unit,
                        num_pallets, stackable, equipment_type,
                        temperature_min_c, temperature_max_c,
                        hazmat_indicator, hazmat_un_number, hazmat_class,
                        special_handling_instructions, notes, created_at)
                    VALUES (:id, :order_number, :source_email_id, 'extracted',
                        :confidence, :mode, :field_scores,
                        :customer_name, :contact_name, :contact_email, :contact_phone,
                        :pickup_location_name, :pickup_address, :pickup_date, :pickup_instructions,
                        :delivery_location_name, :delivery_address, :delivery_date, :delivery_instructions,
                        :customer_order_number, :reference_number, :po_number,
                        :commodity, :freight_type, :total_weight, :weight_unit,
                        :num_pallets, :stackable, :equipment_type,
                        :temp_min, :temp_max,
                        :hazmat, :hazmat_un, :hazmat_class,
                        :special_handling, :notes, NOW())
                """),
                {
                    "id": str(order_id),
                    "order_number": order_number,
                    "source_email_id": email_id,
                    "confidence": overall_confidence,
                    "mode": None,  # Set by validation agent
                    "field_scores": json.dumps(confidence_scores),
                    "customer_name": normalized.get("customer_name"),
                    "contact_name": normalized.get("contact_name"),
                    "contact_email": normalized.get("contact_email"),
                    "contact_phone": normalized.get("contact_phone"),
                    "pickup_location_name": normalized.get("pickup_location_name"),
                    "pickup_address": json.dumps(normalized.get("pickup_address")) if normalized.get("pickup_address") else None,
                    "pickup_date": _parse_date(normalized.get("pickup_date")),
                    "pickup_instructions": normalized.get("pickup_instructions"),
                    "delivery_location_name": normalized.get("delivery_location_name"),
                    "delivery_address": json.dumps(normalized.get("delivery_address")) if normalized.get("delivery_address") else None,
                    "delivery_date": _parse_date(normalized.get("delivery_date")),
                    "delivery_instructions": normalized.get("delivery_instructions"),
                    "customer_order_number": normalized.get("customer_order_number"),
                    "reference_number": normalized.get("reference_number"),
                    "po_number": normalized.get("po_number"),
                    "commodity": normalized.get("commodity"),
                    "freight_type": normalized.get("freight_type"),
                    "total_weight": normalized.get("total_weight"),
                    "weight_unit": normalized.get("weight_unit"),
                    "num_pallets": normalized.get("num_pallets"),
                    "stackable": normalized.get("stackable", False),
                    "equipment_type": normalized.get("equipment_type"),
                    "temp_min": normalized.get("temperature_min_c"),
                    "temp_max": normalized.get("temperature_max_c"),
                    "hazmat": normalized.get("hazmat_indicator", False),
                    "hazmat_un": normalized.get("hazmat_un_number"),
                    "hazmat_class": normalized.get("hazmat_class"),
                    "special_handling": normalized.get("special_handling_instructions"),
                    "notes": normalized.get("notes"),
                },
            )
            # Link email to order
            await session.execute(
                text("UPDATE emails SET linked_order_id = :oid, status = 'processed' WHERE id = :eid"),
                {"oid": str(order_id), "eid": email_id},
            )
            await session.commit()

        # Publish to validation queue
        await adapters.queue.publish_message(
            queue_name="validation",
            body={
                "email_id": email_id,
                "order_id": str(order_id),
                "confidence_scores": confidence_scores,
                "overall_confidence": overall_confidence,
            },
        )

        self.logger.info(
            f"Order {order_number} extracted with {overall_confidence:.1f}% confidence"
        )

    async def _call_llm_with_retry(self, text_content: str, max_retries: int = 2) -> dict | None:
        """Call LLM for extraction with retry on malformed JSON."""
        adapters = get_adapters()

        for attempt in range(max_retries + 1):
            messages = [{"role": "user", "content": f"Extract order data from this text:\n\n{text_content}"}]

            if attempt > 0:
                messages.append({
                    "role": "user",
                    "content": "Your previous response was not valid JSON. Return ONLY a valid JSON object with 'order' and 'confidence_scores' keys.",
                })

            response = await adapters.llm.complete(
                messages=messages,
                system=EXTRACTION_SYSTEM_PROMPT,
                temperature=0,
                max_tokens=4096,
            )

            try:
                # Try to parse JSON from response
                content = response.content.strip()
                # Handle markdown code blocks
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0]
                data = json.loads(content)
                if "order" in data and "confidence_scores" in data:
                    return data
                self.logger.warning(f"LLM response missing required keys, attempt {attempt + 1}")
            except json.JSONDecodeError as e:
                self.logger.warning(f"LLM returned invalid JSON (attempt {attempt + 1}): {e}")

        return None

    def _normalize_fields(self, order_data: dict[str, Any]) -> dict[str, Any]:
        """Apply normalization to extracted field values."""
        normalized = dict(order_data)

        # Normalize dates
        for date_field in ("pickup_date", "delivery_date"):
            if normalized.get(date_field):
                parsed = normalize_date(str(normalized[date_field]))
                normalized[date_field] = parsed.isoformat() if parsed else None

        # Normalize weight
        if normalized.get("total_weight"):
            weight_str = str(normalized["total_weight"])
            if normalized.get("weight_unit"):
                weight_str += f" {normalized['weight_unit']}"
            value, unit = normalize_weight(weight_str)
            normalized["total_weight"] = value
            normalized["weight_unit"] = unit

        # Normalize phone
        if normalized.get("contact_phone"):
            normalized["contact_phone"] = normalize_phone(str(normalized["contact_phone"]))

        # Build address objects
        for prefix in ("pickup", "delivery"):
            addr_fields = {
                "line1": normalized.pop(f"{prefix}_address_line1", None),
                "city": normalized.pop(f"{prefix}_city", None),
                "state": normalized.pop(f"{prefix}_state", None),
                "postal_code": normalized.pop(f"{prefix}_postal_code", None),
                "country": normalized.pop(f"{prefix}_country", None) or "CA",
            }
            if addr_fields["line1"]:
                addr_fields["line1"] = expand_address_abbreviations(addr_fields["line1"]) or addr_fields["line1"]
                normalized[f"{prefix}_address"] = {k: v for k, v in addr_fields.items() if v}
            else:
                normalized[f"{prefix}_address"] = None

        return normalized

    async def _generate_order_number(self) -> str:
        """Generate next order number: ORD-YYYYMMDD-XXXXX."""
        from datetime import date

        today = date.today()
        date_str = today.strftime("%Y%m%d")

        async with async_session_factory() as session:
            result = await session.execute(text("SELECT nextval('order_number_seq')"))
            seq = result.scalar()
            return f"ORD-{date_str}-{seq:05d}"

    async def _process_customer_response(
        self,
        email_id: str,
        email_body: str,
        extraction_results: list,
        related_order_id: str,
    ) -> None:
        """Process a customer response by extracting new fields and merging into existing order."""
        adapters = get_adapters()

        # Combine reply text
        text_parts = []
        if email_body:
            text_parts.append(email_body)
        for ext in extraction_results:
            if ext.get("text"):
                text_parts.append(ext["text"])
        reply_text = "\n".join(text_parts)

        if not reply_text.strip():
            self.logger.warning(f"Empty customer response for order {related_order_id}")
            return

        # Load the existing order to see what fields are missing
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT * FROM orders WHERE id = :id"),
                {"id": related_order_id},
            )
            order = result.mappings().first()
            if not order:
                self.logger.error(f"Related order {related_order_id} not found")
                return

            # Get validation failures to know what was missing
            val_result = await session.execute(
                text("SELECT field_name FROM validation_results WHERE order_id = :id AND status = 'fail'"),
                {"id": related_order_id},
            )
            missing_fields = [row[0] for row in val_result.fetchall()]

        # Ask LLM to extract only the missing fields from the reply
        missing_fields_str = ", ".join(missing_fields) if missing_fields else "any order fields"

        response = await adapters.llm.complete(
            messages=[{"role": "user", "content": f"Extract the following fields from this customer reply:\nFields needed: {missing_fields_str}\n\nCustomer reply:\n{reply_text}"}],
            system=f"""You are extracting specific order field values from a customer's email reply.
The customer was asked to provide missing information for a transportation order.
Extract ONLY the fields listed. Return a JSON object with field names as keys and extracted values.
If a field is not found in the reply, do not include it.
Normalize dates to YYYY-MM-DD format.
Return ONLY valid JSON.""",
            temperature=0,
            max_tokens=1024,
        )

        # Parse extracted fields
        try:
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0]
            extracted_fields = json.loads(content)
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Failed to parse customer response extraction: {e}")
            return

        if not extracted_fields:
            self.logger.info(f"No new fields extracted from customer response")
            return

        # Build UPDATE query for the extracted fields
        update_parts = []
        params: dict = {"id": related_order_id}

        field_to_column = {
            "pickup_date": "pickup_date",
            "delivery_date": "delivery_date",
            "equipment_type": "equipment_type",
            "commodity": "commodity",
            "freight_type": "freight_type",
            "total_weight": "total_weight",
            "weight_unit": "weight_unit",
            "customer_name": "customer_name",
            "contact_name": "contact_name",
            "contact_email": "contact_email",
            "contact_phone": "contact_phone",
            "pickup_location_name": "pickup_location_name",
            "delivery_location_name": "delivery_location_name",
            "num_pallets": "num_pallets",
            "hazmat_un_number": "hazmat_un_number",
            "hazmat_class": "hazmat_class",
            "temperature_min_c": "temperature_min_c",
            "temperature_max_c": "temperature_max_c",
        }

        # Handle address sub-fields
        pickup_addr_updates = {}
        delivery_addr_updates = {}

        for field_name, value in extracted_fields.items():
            if value is None:
                continue

            # Handle pickup address sub-fields
            if field_name in ("pickup_address_line1", "pickup_city", "pickup_state", "pickup_postal_code", "pickup_country"):
                key = field_name.replace("pickup_", "").replace("address_", "")
                pickup_addr_updates[key] = value
            elif field_name in ("delivery_address_line1", "delivery_city", "delivery_state", "delivery_postal_code", "delivery_country"):
                key = field_name.replace("delivery_", "").replace("address_", "")
                delivery_addr_updates[key] = value
            elif field_name in field_to_column:
                col = field_to_column[field_name]
                if "date" in col:
                    # Convert date string to date object
                    params[col] = _parse_date(str(value))
                else:
                    params[col] = value
                update_parts.append(f"{col} = :{col}")

        # Merge address updates into existing JSONB
        if pickup_addr_updates:
            existing_addr = order.get("pickup_address") or {}
            if isinstance(existing_addr, str):
                existing_addr = json.loads(existing_addr)
            existing_addr.update(pickup_addr_updates)
            params["pickup_address"] = json.dumps(existing_addr)
            update_parts.append("pickup_address = :pickup_address::jsonb")

        if delivery_addr_updates:
            existing_addr = order.get("delivery_address") or {}
            if isinstance(existing_addr, str):
                existing_addr = json.loads(existing_addr)
            existing_addr.update(delivery_addr_updates)
            params["delivery_address"] = json.dumps(existing_addr)
            update_parts.append("delivery_address = :delivery_address::jsonb")

        if not update_parts:
            self.logger.info(f"No updatable fields extracted from customer response")
            return

        # Update order and change status back to 'extracted' for re-validation
        update_parts.append("status = 'extracted'")
        update_parts.append("updated_at = NOW()")

        async with async_session_factory() as session:
            await session.execute(
                text(f"UPDATE orders SET {', '.join(update_parts)} WHERE id = :id"),
                params,
            )
            # Log the update in order history
            await session.execute(
                text("""
                    INSERT INTO order_history (id, order_id, event_type, previous_status, new_status, triggered_by, actor_id, detail_json, created_at)
                    VALUES (:hid, :order_id, 'customer_response_merged', 'awaiting_customer', 'extracted', 'agent', :agent, :detail, NOW())
                """),
                {
                    "hid": str(uuid.uuid4()),
                    "order_id": related_order_id,
                    "agent": self.agent_type,
                    "detail": json.dumps({"merged_fields": list(extracted_fields.keys()), "from_email": email_id}),
                },
            )
            # Link this email to the order
            await session.execute(
                text("UPDATE emails SET linked_order_id = :oid, status = 'processed' WHERE id = :eid"),
                {"oid": related_order_id, "eid": email_id},
            )
            await session.commit()

        self.logger.info(
            f"Customer response merged into order {order['order_number']}: "
            f"updated fields {list(extracted_fields.keys())}"
        )

        # Re-validate the order by publishing to validation queue
        # Recompute confidence with the updated fields
        field_scores = order.get("field_confidence_scores") or {}
        if isinstance(field_scores, str):
            try:
                field_scores = json.loads(field_scores)
            except (json.JSONDecodeError, TypeError):
                field_scores = {}

        # Set high confidence for fields just provided by customer
        for f in extracted_fields.keys():
            field_scores[f] = 95.0

        # Also set confidence for fields that already have values on the order
        # (they were extracted originally but scores may have been lost)
        from order_shared.utils.confidence import compute_weighted_confidence
        mandatory_fields = [
            "customer_name", "contact_name", "contact_email",
            "pickup_location_name", "pickup_date",
            "delivery_location_name", "delivery_date",
            "commodity", "freight_type", "total_weight", "weight_unit",
            "equipment_type", "hazmat_indicator",
        ]
        for f in mandatory_fields:
            if f not in field_scores or field_scores[f] == 0:
                # Check if the order already has a value for this field
                order_value = order.get(f)
                if order_value is not None and order_value != "" and order_value is not False:
                    field_scores[f] = 90.0  # Existing value = high confidence

        overall_confidence = compute_weighted_confidence(field_scores, mandatory_fields)

        # Update confidence scores on the order itself
        async with async_session_factory() as session:
            await session.execute(
                text("""
                    UPDATE orders
                    SET field_confidence_scores = CAST(:scores AS jsonb),
                        overall_confidence_score = :confidence
                    WHERE id = :id
                """),
                {
                    "scores": json.dumps(field_scores),
                    "confidence": overall_confidence,
                    "id": related_order_id,
                },
            )
            await session.commit()

        await adapters.queue.publish_message(
            queue_name="validation",
            body={
                "email_id": email_id,
                "order_id": related_order_id,
                "confidence_scores": field_scores,
                "overall_confidence": overall_confidence,
            },
        )

        self.logger.info(
            f"Order {order['order_number']} re-submitted for validation "
            f"(new confidence: {overall_confidence:.1f}%)"
        )


def _parse_date(value: str | None) -> "date | None":
    """Convert a date string (YYYY-MM-DD) to a Python date object for asyncpg."""
    if not value:
        return None
    from datetime import date as date_type

    if isinstance(value, date_type):
        return value
    try:
        return date_type.fromisoformat(str(value))
    except (ValueError, TypeError):
        return None
