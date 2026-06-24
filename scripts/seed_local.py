"""Seed script for local development database.

Populates: customers (20), users (3), business rules (12), email templates (4),
field configurations (60+), and sample orders (5).

Usage: python -m scripts.seed_local
"""

import hashlib
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DATABASE_URL = "postgresql://orderuser:orderpass@localhost:5432/orderdb"


def hash_password(password: str) -> str:
    """Simple SHA-256 hash for local dev passwords (NOT production-grade)."""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_users(session: Session) -> dict[str, uuid.UUID]:
    """Create 3 test users."""
    users = [
        {"email": "agent@test.com", "name": "Alex Agent", "role": "agent", "password": "agent123"},
        {"email": "supervisor@test.com", "name": "Morgan Supervisor", "role": "supervisor", "password": "super123"},
        {"email": "admin@test.com", "name": "Sam Admin", "role": "admin", "password": "admin123"},
    ]
    user_ids = {}
    for u in users:
        uid = uuid.uuid4()
        session.execute(text("""
            INSERT INTO users (id, email, name, role, active, password_hash, created_at)
            VALUES (:id, :email, :name, :role, true, :pw, NOW())
            ON CONFLICT (email) DO NOTHING
        """), {"id": str(uid), "email": u["email"], "name": u["name"], "role": u["role"], "pw": hash_password(u["password"])})
        user_ids[u["role"]] = uid
    return user_ids


def seed_customers(session: Session) -> list[uuid.UUID]:
    """Create 20 sample customer profiles."""
    customers = [
        {"name": "Maple Leaf Foods Inc.", "external_id": "MLF-001", "domains": ["mapleleaf.com"], "always_hitl": False, "equipment": "reefer"},
        {"name": "Canadian Tire Corporation", "external_id": "CTC-002", "domains": ["cantire.com"], "always_hitl": False, "equipment": "dry_van"},
        {"name": "Loblaws Companies", "external_id": "LOB-003", "domains": ["loblaws.ca"], "always_hitl": False, "equipment": "reefer"},
        {"name": "Irving Oil", "external_id": "IRV-004", "domains": ["irvingoil.com"], "always_hitl": True, "equipment": "tanker"},
        {"name": "Suncor Energy", "external_id": "SUN-005", "domains": ["suncor.com"], "always_hitl": True, "equipment": "tanker"},
        {"name": "Home Hardware Stores", "external_id": "HHS-006", "domains": ["homehardware.ca"], "always_hitl": False, "equipment": "dry_van"},
        {"name": "Tim Hortons Distribution", "external_id": "THD-007", "domains": ["timhortons.ca"], "always_hitl": False, "equipment": "reefer"},
        {"name": "Bombardier Transportation", "external_id": "BOM-008", "domains": ["bombardier.com"], "always_hitl": False, "equipment": "flatbed"},
        {"name": "Vale Canada Mining", "external_id": "VCM-009", "domains": ["vale.com"], "always_hitl": True, "equipment": "flatbed"},
        {"name": "Weston Bakeries", "external_id": "WB-010", "domains": ["weston.ca"], "always_hitl": False, "equipment": "reefer"},
        {"name": "Saputo Inc.", "external_id": "SAP-011", "domains": ["saputo.com"], "always_hitl": False, "equipment": "reefer"},
        {"name": "Molson Coors Canada", "external_id": "MCC-012", "domains": ["molsoncoors.com"], "always_hitl": False, "equipment": "dry_van"},
        {"name": "Canfor Corporation", "external_id": "CAN-013", "domains": ["canfor.com"], "always_hitl": False, "equipment": "flatbed"},
        {"name": "Teck Resources", "external_id": "TEC-014", "domains": ["teck.com"], "always_hitl": True, "equipment": "step_deck"},
        {"name": "Purolator Inc.", "external_id": "PUR-015", "domains": ["purolator.com"], "always_hitl": False, "equipment": "dry_van"},
        {"name": "Metro Inc.", "external_id": "MET-016", "domains": ["metro.ca"], "always_hitl": False, "equipment": "reefer"},
        {"name": "Kruger Products", "external_id": "KRU-017", "domains": ["krugerproducts.ca"], "always_hitl": False, "equipment": "dry_van"},
        {"name": "Cascades Inc.", "external_id": "CAS-018", "domains": ["cascades.com"], "always_hitl": False, "equipment": "dry_van"},
        {"name": "Nutrien Ltd.", "external_id": "NUT-019", "domains": ["nutrien.com"], "always_hitl": True, "equipment": "tanker"},
        {"name": "West Fraser Timber", "external_id": "WFT-020", "domains": ["westfraser.com"], "always_hitl": False, "equipment": "flatbed"},
    ]
    customer_ids = []
    for c in customers:
        cid = uuid.uuid4()
        session.execute(text("""
            INSERT INTO customers (id, name, external_id, email_domains, always_human_review, default_equipment_type, created_at)
            VALUES (:id, :name, :ext_id, :domains, :always_hitl, :equipment, NOW())
            ON CONFLICT DO NOTHING
        """), {"id": str(cid), "name": c["name"], "ext_id": c["external_id"],
               "domains": c["domains"], "always_hitl": c["always_hitl"], "equipment": c["equipment"]})
        customer_ids.append(cid)
    return customer_ids


def seed_business_rules(session: Session) -> None:
    """Create 12 default business rules."""
    rules = [
        {"name": "pickup_date_future", "field": "pickup_date", "type": "date_after", "expr": "today", "msg": "Pickup date must be today or in the future", "priority": 1},
        {"name": "delivery_after_pickup", "field": "delivery_date", "type": "date_after", "expr": "pickup_date", "msg": "Delivery date must be on or after pickup date", "priority": 2},
        {"name": "weight_positive", "field": "total_weight", "type": "regex_match", "expr": "^[0-9]+(\\.[0-9]+)?$", "msg": "Total weight must be a positive number", "priority": 3},
        {"name": "email_format", "field": "contact_email", "type": "regex_match", "expr": "^[^@]+@[^@]+\\.[^@]+$", "msg": "Contact email must be a valid email address", "priority": 4},
        {"name": "freight_type_valid", "field": "freight_type", "type": "valid_enum", "expr": "ftl,ltl,partial,intermodal", "msg": "Freight type must be FTL, LTL, Partial, or Intermodal", "priority": 5},
        {"name": "equipment_type_valid", "field": "equipment_type", "type": "valid_enum", "expr": "dry_van,flatbed,reefer,step_deck,tanker,lowboy,conestoga,other", "msg": "Equipment type must be a valid option", "priority": 6},
        {"name": "reefer_temp_required", "field": "temperature_min_c", "type": "required_if", "expr": "equipment_type=reefer", "msg": "Temperature range is required for Reefer equipment", "priority": 7},
        {"name": "hazmat_un_required", "field": "hazmat_un_number", "type": "required_if", "expr": "hazmat_indicator=true", "msg": "UN Number is required for hazardous materials", "priority": 8},
        {"name": "hazmat_class_required", "field": "hazmat_class", "type": "required_if", "expr": "hazmat_indicator=true", "msg": "Hazmat Class is required for hazardous materials", "priority": 9},
        {"name": "pallets_required_ftl", "field": "num_pallets", "type": "required_if", "expr": "freight_type=ftl", "msg": "Number of pallets is required for FTL shipments", "priority": 10},
        {"name": "pallets_required_ltl", "field": "num_pallets", "type": "required_if", "expr": "freight_type=ltl", "msg": "Number of pallets is required for LTL shipments", "priority": 11},
        {"name": "postal_code_format", "field": "pickup_address.postal_code", "type": "regex_match", "expr": "^[A-Z]\\d[A-Z]\\s?\\d[A-Z]\\d$|^\\d{5}(-\\d{4})?$", "msg": "Postal code must be valid Canadian or US format", "priority": 12},
    ]
    for r in rules:
        session.execute(text("""
            INSERT INTO business_rules (id, rule_name, field_name, rule_type, rule_expression, error_message, severity, priority, active, updated_at)
            VALUES (:id, :name, :field, :type, :expr, :msg, 'error', :priority, true, NOW())
            ON CONFLICT DO NOTHING
        """), {"id": str(uuid.uuid4()), "name": r["name"], "field": r["field"],
               "type": r["type"], "expr": r["expr"], "msg": r["msg"], "priority": r["priority"]})


def seed_email_templates(session: Session) -> None:
    """Create 4 default email templates."""
    templates = [
        {
            "type": "missing_info",
            "name": "Missing Information Request",
            "subject": "Action Required: Missing Information for Your Transportation Order",
            "html": "<p>Dear {{customer_name}},</p><p>Thank you for your transportation order request. We are processing your order but require the following information to proceed:</p><ul>{{#each missing_fields}}<li>{{this}}</li>{{/each}}</ul><p>Please reply to this email with the missing details at your earliest convenience.</p><p>Order Reference: {{order_reference}}</p><p>Please respond within 48 hours to avoid delays.</p><p>Best regards,<br>Order Processing Team</p>",
            "text": "Dear {{customer_name}},\n\nThank you for your transportation order request. We require the following information:\n\n{{#each missing_fields}}- {{this}}\n{{/each}}\nPlease reply with the missing details.\n\nOrder Reference: {{order_reference}}\nPlease respond within 48 hours.\n\nBest regards,\nOrder Processing Team",
            "vars": ["customer_name", "missing_fields", "order_reference"],
        },
        {
            "type": "follow_up",
            "name": "Follow-up: Missing Information",
            "subject": "Reminder: Missing Information for Order {{order_reference}}",
            "html": "<p>Dear {{customer_name}},</p><p>This is a friendly reminder that we are still awaiting the following information for your transportation order:</p><ul>{{#each missing_fields}}<li>{{this}}</li>{{/each}}</ul><p>Order Reference: {{order_reference}}</p><p>Please respond at your earliest convenience to avoid further delays.</p><p>Best regards,<br>Order Processing Team</p>",
            "text": "Dear {{customer_name}},\n\nReminder: We are still awaiting the following information:\n\n{{#each missing_fields}}- {{this}}\n{{/each}}\nOrder Reference: {{order_reference}}\n\nPlease respond to avoid delays.\n\nBest regards,\nOrder Processing Team",
            "vars": ["customer_name", "missing_fields", "order_reference"],
        },
        {
            "type": "acknowledgement",
            "name": "Order Acknowledgement",
            "subject": "Order Confirmed: {{order_number}}",
            "html": "<p>Dear {{customer_name}},</p><p>Your transportation order has been successfully created.</p><p><strong>Order Number:</strong> {{order_number}}<br><strong>Pickup Date:</strong> {{pickup_date}}<br><strong>Delivery Date:</strong> {{delivery_date}}<br><strong>Equipment:</strong> {{equipment_type}}</p><p>You will receive updates as your shipment progresses.</p><p>Best regards,<br>Order Processing Team</p>",
            "text": "Dear {{customer_name}},\n\nYour order has been confirmed.\n\nOrder Number: {{order_number}}\nPickup Date: {{pickup_date}}\nDelivery Date: {{delivery_date}}\nEquipment: {{equipment_type}}\n\nBest regards,\nOrder Processing Team",
            "vars": ["customer_name", "order_number", "pickup_date", "delivery_date", "equipment_type"],
        },
        {
            "type": "duplicate_notification",
            "name": "Duplicate Order Detected",
            "subject": "Duplicate Order Detected - Original Order {{original_order_number}} Confirmed",
            "html": "<p>Dear {{customer_name}},</p><p>We detected a duplicate submission matching your existing order.</p><p><strong>Original Order:</strong> {{original_order_number}}<br><strong>Status:</strong> Confirmed and being processed</p><p>If this was intentional and you need a separate order, please reply to this email with confirmation.</p><p>Best regards,<br>Order Processing Team</p>",
            "text": "Dear {{customer_name}},\n\nWe detected a duplicate submission.\n\nOriginal Order: {{original_order_number}}\nStatus: Confirmed\n\nIf you need a separate order, please reply with confirmation.\n\nBest regards,\nOrder Processing Team",
            "vars": ["customer_name", "original_order_number"],
        },
    ]
    for t in templates:
        session.execute(text("""
            INSERT INTO email_templates (id, template_type, name, subject_template, body_html_template, body_text_template, variables, active, updated_at)
            VALUES (:id, :type, :name, :subject, :html, :text, :vars, true, NOW())
            ON CONFLICT DO NOTHING
        """), {"id": str(uuid.uuid4()), "type": t["type"], "name": t["name"],
               "subject": t["subject"], "html": t["html"], "text": t["text"], "vars": t["vars"]})


def seed_field_configurations(session: Session) -> None:
    """Create all 60+ field configurations."""
    fields = [
        # Customer Info
        ("customer_name", "Customer Name", True, False, None, None, 1),
        ("customer_external_id", "Customer ID", False, True, "customer_name", "ambiguous_match", 2),
        ("contact_name", "Contact Name", True, False, None, None, 3),
        ("contact_email", "Contact Email", True, False, None, None, 4),
        ("contact_phone", "Contact Phone", False, False, None, None, 5),
        # Pickup
        ("pickup_location_name", "Pickup Location Name", True, False, None, None, 10),
        ("pickup_address_line1", "Pickup Address", True, False, None, None, 11),
        ("pickup_city", "Pickup City", True, False, None, None, 12),
        ("pickup_state", "Pickup State/Province", True, False, None, None, 13),
        ("pickup_postal_code", "Pickup Postal Code", True, False, None, None, 14),
        ("pickup_country", "Pickup Country", True, False, None, None, 15),
        ("pickup_date", "Pickup Date", True, False, None, None, 16),
        ("pickup_time_start", "Pickup Time Window Start", False, False, None, None, 17),
        ("pickup_time_end", "Pickup Time Window End", False, False, None, None, 18),
        ("pickup_instructions", "Pickup Instructions", False, False, None, None, 19),
        # Delivery
        ("delivery_location_name", "Delivery Location Name", True, False, None, None, 20),
        ("delivery_address_line1", "Delivery Address", True, False, None, None, 21),
        ("delivery_city", "Delivery City", True, False, None, None, 22),
        ("delivery_state", "Delivery State/Province", True, False, None, None, 23),
        ("delivery_postal_code", "Delivery Postal Code", True, False, None, None, 24),
        ("delivery_country", "Delivery Country", True, False, None, None, 25),
        ("delivery_date", "Delivery Date", True, False, None, None, 26),
        ("delivery_time_start", "Delivery Time Window Start", False, False, None, None, 27),
        ("delivery_time_end", "Delivery Time Window End", False, False, None, None, 28),
        ("delivery_instructions", "Delivery Instructions", False, False, None, None, 29),
        # Shipment
        ("customer_order_number", "Customer Order Number", False, False, None, None, 30),
        ("reference_number", "Reference Number", False, False, None, None, 31),
        ("po_number", "PO Number", False, False, None, None, 32),
        ("commodity", "Commodity Description", True, False, None, None, 33),
        ("freight_type", "Freight Type", True, False, None, None, 34),
        ("total_weight", "Total Weight", True, False, None, None, 35),
        ("weight_unit", "Weight Unit", True, False, None, None, 36),
        ("dimensions", "Dimensions (L x W x H)", False, False, None, None, 37),
        ("total_quantity", "Total Quantity / Pieces", False, False, None, None, 38),
        ("num_pallets", "Number of Pallets", False, True, "freight_type", "ftl,ltl", 39),
        ("stackable", "Stackable", False, False, None, None, 40),
        # Transportation
        ("equipment_type", "Equipment Type", True, False, None, None, 50),
        ("truck_size", "Truck Size", False, False, None, None, 51),
        ("temperature_min_c", "Temperature Min (C)", False, True, "equipment_type", "reefer", 52),
        ("temperature_max_c", "Temperature Max (C)", False, True, "equipment_type", "reefer", 53),
        ("hazmat_indicator", "Hazmat Indicator", True, False, None, None, 54),
        ("hazmat_un_number", "UN Number", False, True, "hazmat_indicator", "true", 55),
        ("hazmat_class", "Hazmat Class", False, True, "hazmat_indicator", "true", 56),
        ("special_handling_instructions", "Special Handling Instructions", False, False, None, None, 57),
        ("liftgate_required", "Liftgate Required", False, False, None, None, 58),
        ("team_drive_required", "Team Drive Required", False, False, None, None, 59),
        ("twic_card_required", "TWIC Card Required", False, False, None, None, 60),
        # Additional
        ("notes", "General Notes", False, False, None, None, 70),
        ("internal_comments", "Internal Comments", False, False, None, None, 71),
    ]
    for f in fields:
        session.execute(text("""
            INSERT INTO field_configurations (id, field_name, label, is_mandatory, is_conditional, conditional_depends_on, conditional_value, display_order, active)
            VALUES (:id, :field_name, :label, :mandatory, :conditional, :depends_on, :cond_value, :order, true)
            ON CONFLICT (field_name) DO NOTHING
        """), {"id": str(uuid.uuid4()), "field_name": f[0], "label": f[1],
               "mandatory": f[2], "conditional": f[3], "depends_on": f[4],
               "cond_value": f[5], "order": f[6]})


def seed_sample_orders(session: Session, customer_ids: list[uuid.UUID]) -> None:
    """Create 5 sample orders in various statuses."""
    orders = [
        {"number": "ORD-20260620-00001", "status": "order_created", "confidence": 97.5, "mode": "auto", "commodity": "Frozen Chicken Products", "freight": "ftl", "equipment": "reefer"},
        {"number": "ORD-20260620-00002", "status": "pending_review", "confidence": 85.0, "mode": "hitl_review", "commodity": "Industrial Steel Coils", "freight": "ftl", "equipment": "flatbed"},
        {"number": "ORD-20260621-00001", "status": "awaiting_customer", "confidence": 72.0, "mode": "hitl_review", "commodity": "Various Machine Components", "freight": "ltl", "equipment": "dry_van"},
        {"number": "ORD-20260622-00001", "status": "extracted", "confidence": 91.0, "mode": "auto", "commodity": "Fresh Produce - Mixed Vegetables", "freight": "ltl", "equipment": "reefer"},
        {"number": "ORD-20260622-00002", "status": "failed", "confidence": 45.0, "mode": "manual_entry", "commodity": "Unknown cargo", "freight": None, "equipment": None},
    ]
    for i, o in enumerate(orders):
        cid = customer_ids[i % len(customer_ids)]
        session.execute(text("""
            INSERT INTO orders (id, order_number, customer_id, status, overall_confidence_score, processing_mode, commodity, freight_type, equipment_type, created_at)
            VALUES (:id, :num, :cid, :status, :conf, :mode, :commodity, :freight, :equipment, NOW())
            ON CONFLICT (order_number) DO NOTHING
        """), {"id": str(uuid.uuid4()), "num": o["number"], "cid": str(cid),
               "status": o["status"], "conf": o["confidence"], "mode": o["mode"],
               "commodity": o["commodity"], "freight": o["freight"], "equipment": o["equipment"]})


def main() -> None:
    """Run all seed functions."""
    import os
    db_url = os.environ.get("DATABASE_URL_SYNC", DATABASE_URL)
    engine = create_engine(db_url)
    with Session(engine) as session:
        print("Seeding users...")
        user_ids = seed_users(session)

        print("Seeding customers (20)...")
        customer_ids = seed_customers(session)

        print("Seeding business rules (12)...")
        seed_business_rules(session)

        print("Seeding email templates (4)...")
        seed_email_templates(session)

        print("Seeding field configurations (49)...")
        seed_field_configurations(session)

        print("Seeding sample orders (5)...")
        seed_sample_orders(session, customer_ids)

        session.commit()
        print("Seed complete!")


if __name__ == "__main__":
    import os
    db_url = os.environ.get("DATABASE_URL_SYNC", DATABASE_URL)
    DATABASE_URL = db_url
    main()
