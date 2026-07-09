"""Generate presentation for Order Intelligence Agent platform."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.33)
prs.slide_height = Inches(7.5)

# Colors
NAVY = RGBColor(0x0F, 0x1B, 0x2D)
AMBER = RGBColor(0xF5, 0x9E, 0x0B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY = RGBColor(0x64, 0x74, 0x8B)
LIGHT_BG = RGBColor(0xF8, 0xFA, 0xFC)
DARK_TEXT = RGBColor(0x1E, 0x29, 0x3B)
GREEN = RGBColor(0x10, 0xB9, 0x81)


def add_title_slide(title, subtitle):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank
    # Navy background
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = NAVY

    # Title
    txBox = slide.shapes.add_textbox(Inches(1), Inches(2.5), Inches(11), Inches(1.5))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(44)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

    # Subtitle
    txBox2 = slide.shapes.add_textbox(Inches(2), Inches(4.2), Inches(9), Inches(1))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = subtitle
    p2.font.size = Pt(20)
    p2.font.color.rgb = AMBER
    p2.alignment = PP_ALIGN.CENTER

    # Footer
    txBox3 = slide.shapes.add_textbox(Inches(4), Inches(6.5), Inches(5), Inches(0.5))
    tf3 = txBox3.text_frame
    p3 = tf3.paragraphs[0]
    p3.text = "Powered by ideyaLabs"
    p3.font.size = Pt(12)
    p3.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    p3.alignment = PP_ALIGN.CENTER
    return slide


def add_content_slide(title, bullets, note=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank

    # Title bar
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.33), Inches(1.2))
    shape.fill.solid()
    shape.fill.fore_color.rgb = NAVY
    shape.line.fill.background()

    txBox = slide.shapes.add_textbox(Inches(0.8), Inches(0.2), Inches(11), Inches(0.9))
    tf = txBox.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE

    # Content
    txBox2 = slide.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.5), Inches(5.5))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True

    for i, bullet in enumerate(bullets):
        if i > 0:
            p = tf2.add_paragraph()
        else:
            p = tf2.paragraphs[0]

        if bullet.startswith("##"):
            p.text = bullet[2:].strip()
            p.font.size = Pt(18)
            p.font.bold = True
            p.font.color.rgb = NAVY
            p.space_before = Pt(16)
        elif bullet.startswith("- "):
            p.text = bullet[2:]
            p.font.size = Pt(16)
            p.font.color.rgb = DARK_TEXT
            p.level = 1
            p.space_before = Pt(6)
        else:
            p.text = bullet
            p.font.size = Pt(16)
            p.font.color.rgb = DARK_TEXT
            p.space_before = Pt(8)

    if note:
        txBox3 = slide.shapes.add_textbox(Inches(0.8), Inches(6.8), Inches(11), Inches(0.5))
        tf3 = txBox3.text_frame
        p3 = tf3.paragraphs[0]
        p3.text = note
        p3.font.size = Pt(11)
        p3.font.italic = True
        p3.font.color.rgb = GRAY

    return slide


# ═══════════════════════════════════════════════════════════════════
# SLIDES
# ═══════════════════════════════════════════════════════════════════

# Slide 1: Title
add_title_slide(
    "Order Intelligence Agent",
    "AI-Powered Order Intake & Automation for Transportation & Logistics"
)

# Slide 2: Problem Statement
add_content_slide("The Challenge", [
    "## Current State",
    "- Manual order entry from emails: 5-15 minutes per order",
    "- High error rates from manual data transcription",
    "- No standardized process — each agent handles orders differently",
    "- Customer follow-ups are reactive, not proactive",
    "- Limited visibility into pipeline status and STP rates",
    "",
    "## Business Impact",
    "- 40-60% of operations team time spent on data entry",
    "- Order processing delays affect customer satisfaction",
    "- Revenue leakage from missed or duplicate orders",
    "- Inability to scale without adding headcount",
])

# Slide 3: Solution Overview
add_content_slide("Solution: Order Intelligence Agent", [
    "## What It Does",
    "- Monitors email inbox for inbound shipment requests (24/7)",
    "- Extracts order data using AI (GPT-4o) with 99%+ accuracy",
    "- Validates against configurable business rules automatically",
    "- Routes by confidence: auto-process (>=90%) or human review",
    "- Communicates with customers for missing information",
    "- Creates orders automatically — Straight-Through Processing (STP)",
    "",
    "## Key Differentiators",
    "- Handles PDF, Excel, Word, image attachments (OCR)",
    "- Maintains email threading (replies in same conversation)",
    "- Configurable — field rules, thresholds adjusted at runtime",
    "- Full audit trail — every action logged and traceable",
])

# Slide 4: Architecture
add_content_slide("Platform Architecture", [
    "## 6 AI Agents (Event-Driven Pipeline)",
    "- Email Intake Agent — polls inbox, classifies emails (new_order/reply/other)",
    "- Document Understanding Agent — extracts text from attachments (PDF/images/Excel)",
    "- Order Extraction Agent — LLM-powered field extraction with confidence scores",
    "- Validation Agent — mandatory field checks, business rules, duplicate detection",
    "- Communication Agent — auto-emails customers for missing info + follow-ups",
    "- Order Creation Agent — finalizes orders, sends confirmations",
    "",
    "## Tech Stack",
    "- Backend: Python 3.12 + FastAPI (async) | Frontend: React 18 + TypeScript",
    "- Database: PostgreSQL 16 (pgvector) | Cache: Redis 7",
    "- LLM: OpenAI GPT-4o | Email: Microsoft Graph API",
    "- Infrastructure: Docker Compose (on-premise ready)",
], note="Adapter pattern enables swap to AWS (SQS, S3, Textract, Bedrock) without code changes")

# Slide 5: Processing Flow
add_content_slide("Order Processing Flow", [
    "## Email Received → Order Created in ~10 seconds",
    "",
    "1. Email arrives → Intake Agent classifies (new_order vs reply vs spam)",
    "2. Attachments processed → OCR extracts text from PDFs/images",
    "3. GPT-4o extracts all fields with per-field confidence scores",
    "4. Validation checks: 24 mandatory fields, 12 business rules, duplicates",
    "5. Routing decision based on confidence:",
    "   - ≥90% + all fields → Auto-process (STP)",
    "   - 80-90% → Human-in-the-Loop review queue",
    "   - Missing fields → Auto-email customer for clarification",
    "   - Hazmat → Always human review",
    "6. Order created → Confirmation email sent to customer",
    "",
    "## Real Test Result",
    "- Maple Leaf Foods shipment email → 99.2% confidence → auto-created in 9 seconds",
])

# Slide 6: Web Application
add_content_slide("Web Application — Order Entry Platform", [
    "## Dashboard",
    "- Real-time KPIs: Total Orders, STP Rate, Avg E2E Time, Accuracy",
    "- Order status distribution (donut chart), pipeline breakdown (bars)",
    "- STP trend chart (7/14/30 day toggle with 80% target line)",
    "",
    "## Order Management",
    "- Dynamic order form — fields configured by admin (49 fields, 4-step wizard)",
    "- Inline editing on order detail page",
    "- Filter by status, pagination, confidence indicators",
    "",
    "## Operations",
    "- Review Queue — approve/reject orders requiring human review",
    "- Email Inbox — view all processed emails with classification",
    "- Audit Logs — full traceability with search, pagination, JSON diff",
    "",
    "## Administration",
    "- Field Configuration, Business Rules, Email Templates, User Management",
])

# Slide 7: Intelligent Features
add_content_slide("Intelligent Features", [
    "## AI-Powered Extraction",
    "- Per-field confidence scoring (0-100%) for every extracted value",
    "- Handles unstructured emails, PDFs, images, Excel, Word documents",
    "- Equipment type detection, address decomposition, date normalization",
    "",
    "## Smart Routing",
    "- Configurable thresholds (auto-process: 90%, HITL: 80%, communication: 70%)",
    "- Hazmat orders always flagged for human review",
    "- Duplicate detection (same customer + pickup date within 72h window)",
    "",
    "## Automated Customer Communication",
    "- Missing mandatory fields → auto-email customer with specific questions",
    "- Follow-up reminders if no response within 24 hours",
    "- Escalation to human after 2 failed attempts",
    "- Maintains email thread (replies in same Outlook conversation)",
])

# Slide 8: Admin & Configuration
add_content_slide("Runtime Configuration (No Code Changes)", [
    "## Field Configuration (49 fields)",
    "- Toggle mandatory/optional per field at runtime",
    "- Conditional fields (e.g., temperature only for Reefer equipment)",
    "- Display order controls form layout",
    "",
    "## Business Rules (12 active rules)",
    "- date_after: pickup must be future, delivery after pickup",
    "- valid_enum: freight type, equipment type validation",
    "- regex_match: email format, postal codes, weight format",
    "- required_if: temperature required for reefer, UN# for hazmat",
    "",
    "## Email Templates (4 types)",
    "- Missing info request, follow-up reminder, acknowledgement, duplicate alert",
    "- Variable substitution: {{order_number}}, {{customer_name}}, {{missing_fields}}",
    "",
    "## User Management",
    "- 4 roles: Readonly → Agent → Supervisor → Admin",
    "- Create/edit/deactivate users, password management",
])

# Slide 9: Security & Quality
add_content_slide("Security, Quality & Testing", [
    "## Role-Based Access Control",
    "- 4-tier role hierarchy enforced at API + UI level",
    "- JWT authentication with configurable expiry",
    "- Endpoint-level authorization decorators",
    "",
    "## Testing (197 automated tests)",
    "- 26 Playwright E2E tests (UI flows, RBAC, form validation)",
    "- 171 pytest API integration tests:",
    "   - Field-level validation (61 tests — every mandatory, enum, conditional)",
    "   - Admin CRUD (48 tests — configs, rules, templates, users)",
    "   - Auth, orders, reports, queues, conversations (62 tests)",
    "",
    "## Audit & Compliance",
    "- Immutable audit trail (append-only order_history table)",
    "- Every agent action logged with timestamps and context",
    "- Searchable audit logs with export to CSV",
])

# Slide 10: Deployment
add_content_slide("Deployment & Infrastructure", [
    "## On-Premise Deployment (Current)",
    "- Single command: docker compose up -d",
    "- 8 containers: Postgres, Redis, ElasticMQ, MinIO, Mailpit, API, Agents, Frontend",
    "- Requirements: Docker, 8GB RAM, outbound internet (OpenAI + MS Graph)",
    "",
    "## AWS Cloud Path (Future)",
    "- Adapter pattern allows zero-code-change migration:",
    "   - ElasticMQ → Amazon SQS",
    "   - MinIO → Amazon S3",
    "   - Local OCR → AWS Textract",
    "   - OpenAI → AWS Bedrock (Claude)",
    "   - Local JWT → Amazon Cognito",
    "- CDK infrastructure-as-code ready",
    "",
    "## Monitoring",
    "- Health endpoint with DB/Redis/Queue status checks",
    "- Structured JSON logging across all agents",
    "- Docker log aggregation compatible (ELK, CloudWatch)",
])

# Slide 11: Results & Metrics
add_content_slide("Results & Key Metrics", [
    "## Performance (Observed in Testing)",
    "- End-to-end processing time: ~9 seconds (email to order created)",
    "- Extraction accuracy: 99.2% on well-structured emails",
    "- Auto-process rate: 90%+ for complete orders",
    "",
    "## Operational Impact (Projected)",
    "- 80-90% reduction in manual data entry time",
    "- 24/7 automated processing (no staffing dependency)",
    "- Consistent quality — same rules applied every time",
    "- Proactive customer communication (no missed follow-ups)",
    "",
    "## Platform Coverage",
    "- 45 API endpoints, fully tested",
    "- 49 configurable order fields",
    "- 12 business validation rules",
    "- 4 email template types",
    "- Supports PDF, Excel, Word, image attachments",
])

# Slide 12: Roadmap
add_content_slide("Roadmap", [
    "## Phase 1 — Hardening (Next)",
    "- CI/CD pipeline (GitHub Actions)",
    "- Database migrations (Alembic)",
    "- Rate limiting, input sanitization",
    "",
    "## Phase 2 — AWS Cloud Migration",
    "- ECS Fargate, RDS, SQS, S3, Textract, Cognito",
    "- CDK infrastructure-as-code deployment",
    "",
    "## Phase 3 — Advanced Features",
    "- Real-time WebSocket notifications",
    "- pgvector embedding-based duplicate detection",
    "- Customer profile management (preferred lanes, always-HITL flag)",
    "",
    "## Phase 4 — Enterprise",
    "- Multi-tenant support, SSO (SAML/OIDC)",
    "- Data retention policies, API versioning",
    "- CloudWatch dashboards, X-Ray distributed tracing",
])

# Slide 13: Thank You
add_title_slide(
    "Thank You",
    "Order Intelligence Agent — Built by ideyaLabs"
)

# Save
output_path = "/Users/bharathm/BisonTransport/Order_Intelligence_Agent_Presentation.pptx"
prs.save(output_path)
print(f"Presentation saved: {output_path}")
print(f"Total slides: {len(prs.slides)}")
