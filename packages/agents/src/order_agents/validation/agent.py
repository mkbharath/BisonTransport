"""Validation Agent — validates orders and routes by confidence.

Checks mandatory fields, applies business rules, detects duplicates,
and routes orders to auto-process, HITL, communication, or exception queues.
"""

import json
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text

from order_shared.adapters import get_adapters
from order_shared.adapters.base import QueueMessage
from order_shared.db.session import async_session_factory
from order_shared.models.enums import AgentType, OrderStatus
from order_shared.utils.confidence import route_by_confidence
from order_agents.base_agent import BaseAgent


class ValidationAgent(BaseAgent):
    """Validates extracted order data and routes based on confidence."""

    agent_type = AgentType.VALIDATION
    input_queue = "validation"

    async def process_message(self, message: QueueMessage) -> None:
        adapters = get_adapters()
        email_id = message.body["email_id"]
        order_id = message.body["order_id"]
        confidence_scores = message.body.get("confidence_scores", {})
        overall_confidence = message.body.get("overall_confidence", 0)

        # Load order from DB
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT * FROM orders WHERE id = :id"), {"id": order_id}
            )
            order_row = result.mappings().fetchone()
            if not order_row:
                self.logger.error(f"Order {order_id} not found")
                return

        # Load field configurations (mandatory fields)
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT field_name, is_mandatory, is_conditional, conditional_depends_on, conditional_value FROM field_configurations WHERE active = true")
            )
            field_configs = result.mappings().fetchall()

        # Load business rules
        async with async_session_factory() as session:
            result = await session.execute(
                text("SELECT * FROM business_rules WHERE active = true ORDER BY priority")
            )
            rules = result.mappings().fetchall()

        # Run validations
        validation_results: list[dict[str, Any]] = []

        # 1. Mandatory field check
        missing_mandatory = self._check_mandatory_fields(order_row, field_configs, validation_results)

        # 2. Business rule validation
        self._apply_business_rules(order_row, rules, validation_results)

        # 3. Duplicate detection
        is_duplicate = await self._check_duplicate(order_row)
        if is_duplicate:
            validation_results.append({
                "field_name": "_duplicate",
                "rule_name": "duplicate_detection",
                "status": "warning",
                "message": "Potential duplicate order detected",
            })

        # Persist validation results (clear old results first)
        async with async_session_factory() as session:
            await session.execute(
                text("DELETE FROM validation_results WHERE order_id = :order_id"),
                {"order_id": order_id},
            )
            for vr in validation_results:
                await session.execute(
                    text("""
                        INSERT INTO validation_results (id, order_id, field_name, rule_name, status, message, evaluated_at)
                        VALUES (:id, :order_id, :field_name, :rule_name, :status, :message, NOW())
                    """),
                    {"id": str(uuid.uuid4()), "order_id": order_id, **vr},
                )
            await session.commit()

        # Check customer profile for always_hitl
        customer_always_hitl = False
        if order_row.get("customer_id"):
            async with async_session_factory() as session:
                result = await session.execute(
                    text("SELECT always_human_review FROM customers WHERE id = :id"),
                    {"id": str(order_row["customer_id"])},
                )
                cust_row = result.fetchone()
                if cust_row:
                    customer_always_hitl = cust_row[0]

        # Route by confidence
        has_missing = len(missing_mandatory) > 0
        is_hazmat = bool(order_row.get("hazmat_indicator"))

        route = route_by_confidence(
            overall_confidence=overall_confidence,
            has_missing_mandatory=has_missing,
            is_duplicate=is_duplicate,
            is_hazmat=is_hazmat,
            customer_always_hitl=customer_always_hitl,
        )

        # Determine processing mode
        if route.target_queue == "auto-process":
            processing_mode = "auto"
        elif route.target_queue in ("hitl", "exception"):
            processing_mode = "hitl_review"
        else:
            processing_mode = "hitl_review"

        # Update order status
        new_status = self._get_status_for_route(route.target_queue, has_missing)

        async with async_session_factory() as session:
            await session.execute(
                text("""
                    UPDATE orders SET status = :status, processing_mode = :mode, updated_at = NOW()
                    WHERE id = :id
                """),
                {"status": new_status, "mode": processing_mode, "id": order_id},
            )
            # Log to order history
            await session.execute(
                text("""
                    INSERT INTO order_history (id, order_id, event_type, previous_status, new_status, triggered_by, actor_id, detail_json, created_at)
                    VALUES (:id, :order_id, 'validation_complete', 'extracted', :new_status, 'agent', :agent, :detail, NOW())
                """),
                {
                    "id": str(uuid.uuid4()),
                    "order_id": order_id,
                    "new_status": new_status,
                    "agent": self.agent_type,
                    "detail": json.dumps({"route": route.target_queue, "reason": route.reason, "confidence": overall_confidence}),
                },
            )
            await session.commit()

        # Publish to target queue
        await adapters.queue.publish_message(
            queue_name=route.target_queue,
            body={
                "email_id": email_id,
                "order_id": order_id,
                "overall_confidence": overall_confidence,
                "missing_fields": missing_mandatory,
                "hitl_queue_type": route.hitl_queue_type,
                "is_duplicate": is_duplicate,
            },
        )

        self.logger.info(
            f"Order {order_id} routed to '{route.target_queue}': {route.reason}"
        )

    def _check_mandatory_fields(
        self, order: Any, field_configs: list, results: list[dict]
    ) -> list[str]:
        """Check all mandatory fields are present."""
        missing = []
        for fc in field_configs:
            if not fc["is_mandatory"]:
                continue
            field_name = fc["field_name"]
            # Map field config names to order column names
            value = self._get_field_value(order, field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field_name)
                results.append({
                    "field_name": field_name,
                    "rule_name": "mandatory_field",
                    "status": "fail",
                    "message": f"Mandatory field '{field_name}' is missing or empty",
                })
            else:
                results.append({
                    "field_name": field_name,
                    "rule_name": "mandatory_field",
                    "status": "pass",
                    "message": None,
                })
        return missing

    def _get_field_value(self, order: Any, field_name: str) -> Any:
        """Get a field value from the order row, handling nested address fields."""
        import json as json_mod

        # Map field config sub-field names to JSONB address columns
        address_field_map = {
            "pickup_address_line1": ("pickup_address", "line1"),
            "pickup_city": ("pickup_address", "city"),
            "pickup_state": ("pickup_address", "state"),
            "pickup_postal_code": ("pickup_address", "postal_code"),
            "pickup_country": ("pickup_address", "country"),
            "delivery_address_line1": ("delivery_address", "line1"),
            "delivery_city": ("delivery_address", "city"),
            "delivery_state": ("delivery_address", "state"),
            "delivery_postal_code": ("delivery_address", "postal_code"),
            "delivery_country": ("delivery_address", "country"),
        }

        if field_name in address_field_map:
            col, key = address_field_map[field_name]
            addr = order.get(col)
            if addr is None:
                return None
            if isinstance(addr, str):
                try:
                    addr = json_mod.loads(addr)
                except (json_mod.JSONDecodeError, TypeError):
                    return None
            return addr.get(key) if isinstance(addr, dict) else None

        # Direct column mapping
        direct_map = {
            "pickup_date": "pickup_date",
            "delivery_date": "delivery_date",
            "commodity": "commodity",
            "freight_type": "freight_type",
            "total_weight": "total_weight",
            "weight_unit": "weight_unit",
            "equipment_type": "equipment_type",
            "hazmat_indicator": "hazmat_indicator",
            "customer_name": "customer_name",
            "contact_name": "contact_name",
            "contact_email": "contact_email",
            "contact_phone": "contact_phone",
            "pickup_location_name": "pickup_location_name",
            "delivery_location_name": "delivery_location_name",
            "num_pallets": "num_pallets",
            "customer_order_number": "customer_order_number",
            "reference_number": "reference_number",
            "po_number": "po_number",
            "hazmat_un_number": "hazmat_un_number",
            "hazmat_class": "hazmat_class",
            "temperature_min_c": "temperature_min_c",
            "temperature_max_c": "temperature_max_c",
        }
        if field_name in direct_map:
            return order.get(direct_map[field_name])
        # Fallback: check as-is
        return order.get(field_name)

    def _apply_business_rules(
        self, order: Any, rules: list, results: list[dict]
    ) -> None:
        """Apply business rules in priority order."""
        for rule in rules:
            rule_type = rule["rule_type"]
            field_name = rule["field_name"]
            expression = rule["rule_expression"]

            if rule_type == "required_if":
                self._eval_required_if(order, rule, results)
            elif rule_type == "valid_enum":
                self._eval_valid_enum(order, rule, results)
            elif rule_type == "date_after":
                self._eval_date_after(order, rule, results)

    def _eval_required_if(self, order: Any, rule: Any, results: list[dict]) -> None:
        """Evaluate required_if rule: field required when condition met."""
        field_name = rule["field_name"]
        expr = rule["rule_expression"]  # e.g. "equipment_type=reefer"
        parts = expr.split("=", 1)
        if len(parts) != 2:
            return
        dep_field, dep_value = parts
        actual_dep = order.get(dep_field)
        if str(actual_dep).lower() == dep_value.lower():
            value = order.get(field_name)
            if not value:
                results.append({
                    "field_name": field_name,
                    "rule_name": rule["rule_name"],
                    "status": "fail",
                    "message": rule["error_message"],
                })

    def _eval_valid_enum(self, order: Any, rule: Any, results: list[dict]) -> None:
        """Evaluate valid_enum rule."""
        field_name = rule["field_name"]
        value = order.get(field_name)
        if not value:
            return
        valid_values = [v.strip() for v in rule["rule_expression"].split(",")]
        if str(value).lower() not in [v.lower() for v in valid_values]:
            results.append({
                "field_name": field_name,
                "rule_name": rule["rule_name"],
                "status": "fail",
                "message": rule["error_message"],
            })

    def _eval_date_after(self, order: Any, rule: Any, results: list[dict]) -> None:
        """Evaluate date_after rule (e.g., pickup_date must be after today)."""
        field_name = rule["field_name"]
        value = order.get(field_name)
        if not value:
            return
        # Comparison target
        expr = rule["rule_expression"]
        if expr == "today":
            compare_date = date.today()
        elif expr in order:
            compare_date = order.get(expr)
            if not compare_date:
                return
        else:
            return

        if isinstance(value, str):
            from order_shared.utils.normalizers import normalize_date
            value = normalize_date(value)
        if value and value < compare_date:
            results.append({
                "field_name": field_name,
                "rule_name": rule["rule_name"],
                "status": "fail",
                "message": rule["error_message"],
            })

    async def _check_duplicate(self, order: Any) -> bool:
        """Check for duplicate orders within the detection window.

        Matches by: customer_name + pickup_date + delivery postal code within window.
        Falls back to customer_name if customer_id is not set.
        """
        import os
        window_hours = int(os.environ.get("DUPLICATE_DETECTION_WINDOW_HOURS", "72"))

        customer_id = order.get("customer_id")
        customer_name = order.get("customer_name")
        pickup_date = order.get("pickup_date")
        delivery_address = order.get("delivery_address")

        # Need at least customer identifier + pickup date
        if not pickup_date:
            return False
        if not customer_id and not customer_name:
            return False

        # Extract delivery postal code
        delivery_postal = None
        if delivery_address:
            if isinstance(delivery_address, str):
                try:
                    addr = json.loads(delivery_address)
                    delivery_postal = addr.get("postal_code")
                except json.JSONDecodeError:
                    pass
            elif isinstance(delivery_address, dict):
                delivery_postal = delivery_address.get("postal_code")

        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)

        async with async_session_factory() as session:
            # Match by customer_id if available, otherwise by customer_name
            if customer_id:
                query = """
                    SELECT COUNT(*) FROM orders
                    WHERE customer_id = :customer_match
                    AND pickup_date = :pickup_date
                    AND created_at > :cutoff
                    AND id != :order_id
                    AND status != 'cancelled'
                """
                params = {
                    "customer_match": str(customer_id),
                    "pickup_date": pickup_date,
                    "cutoff": cutoff,
                    "order_id": str(order.get("id", "")),
                }
            else:
                query = """
                    SELECT COUNT(*) FROM orders
                    WHERE LOWER(customer_name) = LOWER(:customer_match)
                    AND pickup_date = :pickup_date
                    AND created_at > :cutoff
                    AND id != :order_id
                    AND status != 'cancelled'
                """
                params = {
                    "customer_match": customer_name,
                    "pickup_date": pickup_date,
                    "cutoff": cutoff,
                    "order_id": str(order.get("id", "")),
                }

            # If we have delivery postal code, add it as an extra match condition
            if delivery_postal:
                query = query.replace(
                    "AND status != 'cancelled'",
                    "AND delivery_address->>'postal_code' = :postal AND status != 'cancelled'"
                )
                params["postal"] = delivery_postal

            result = await session.execute(text(query), params)
            count = result.scalar()
            return (count or 0) > 0

    def _get_status_for_route(self, target_queue: str, has_missing: bool) -> str:
        """Map routing target to order status."""
        if target_queue == "auto-process":
            return "validated"
        elif target_queue == "communication":
            return "awaiting_customer"
        else:
            return "pending_review"
