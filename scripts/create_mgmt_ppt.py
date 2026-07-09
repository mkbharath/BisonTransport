"""Generate exec-quality Management PPT using ideyaLabs template.
Follows template styling: Poppins font, #285D93 primary blue, rounded elements.
Includes visual architecture diagram built with shapes.
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from copy import deepcopy
import os

# Load template (preserves master slide branding/logo)
prs = Presentation("ideyalabs PPT template.pptx")

# Remove existing slides but keep slide master
while len(prs.slides) > 0:
    rId = prs.slides._sldIdLst[0].rId
    prs.part.drop_rel(rId)
    del prs.slides._sldIdLst[0]

# Template constants
TITLE_LAYOUT = prs.slide_layouts[0]
CONTENT_LAYOUT = prs.slide_layouts[1]
SECTION_LAYOUT = prs.slide_layouts[2]
TWO_COL_LAYOUT = prs.slide_layouts[3]
BLANK_LAYOUT = prs.slide_layouts[6]
TITLE_ONLY_LAYOUT = prs.slide_layouts[5]

# Brand colors from template
PRIMARY = RGBColor(0x28, 0x5D, 0x93)    # ideyaLabs blue
ACCENT = RGBColor(0xF5, 0x9E, 0x0B)     # Amber/Orange
DARK = RGBColor(0x1A, 0x1A, 0x2E)       # Dark navy
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF1, 0xF5, 0xF9)
TEXT_DARK = RGBColor(0x33, 0x33, 0x33)
TEXT_GRAY = RGBColor(0x66, 0x66, 0x66)
GREEN = RGBColor(0x10, 0xB9, 0x81)
FONT = "Poppins"


def set_font(run, name=FONT, size=Pt(14), bold=False, color=TEXT_DARK):
    run.font.name = name
    run.font.size = size
    run.font.bold = bold
    run.font.color.rgb = color


def add_rounded_box(slide, left, top, width, height, text, fill_color=PRIMARY, font_color=WHITE, font_size=Pt(11), bold=True):
    """Add a rounded rectangle with centered text."""
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    shape.shadow.inherit = False
    tf = shape.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = text
    set_font(run, size=font_size, bold=bold, color=font_color)
    return shape


def add_arrow(slide, start_left, start_top, end_left, end_top, color=PRIMARY):
    """Add a connector arrow."""
    connector = slide.shapes.add_connector(
        1,  # straight connector
        start_left, start_top, end_left, end_top
    )
    connector.line.color.rgb = color
    connector.line.width = Pt(2)
    return connector


def add_exec_title_slide(title, subtitle):
    """Title slide matching template style - rounded rect title."""
    slide = prs.slides.add_slide(BLANK_LAYOUT)
    # Title in rounded rectangle (matching template Slide 1 style)
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(1.2), Inches(2.8), Inches(10.8), Inches(1.8)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = PRIMARY
    shape.line.fill.background()
    tf = shape.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = title
    set_font(run, size=Pt(32), bold=True, color=WHITE)

    # Subtitle below
    txBox = slide.shapes.add_textbox(Inches(2), Inches(5.0), Inches(9), Inches(1.2))
    tf2 = txBox.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.alignment = PP_ALIGN.CENTER
    run2 = p2.add_run()
    run2.text = subtitle
    set_font(run2, size=Pt(16), color=TEXT_GRAY)
    return slide


def add_exec_content_slide(title, content_lines):
    """Content slide with branded title bar."""
    slide = prs.slides.add_slide(BLANK_LAYOUT)

    # Title bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.33), Inches(1.1))
    bar.fill.solid()
    bar.fill.fore_color.rgb = PRIMARY
    bar.line.fill.background()
    txBox = slide.shapes.add_textbox(Inches(0.7), Inches(0.15), Inches(11), Inches(0.8))
    tf = txBox.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = title
    set_font(run, size=Pt(24), bold=True, color=WHITE)

    # Content area
    txBox2 = slide.shapes.add_textbox(Inches(0.8), Inches(1.4), Inches(11.7), Inches(5.8))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True

    for i, line in enumerate(content_lines):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        if line.startswith("##"):
            run = p.add_run()
            run.text = line[2:].strip()
            set_font(run, size=Pt(16), bold=True, color=PRIMARY)
            p.space_before = Pt(14)
        elif line.startswith("- "):
            p.level = 1
            run = p.add_run()
            run.text = line[2:]
            set_font(run, size=Pt(13), color=TEXT_DARK)
            p.space_before = Pt(4)
        elif line.startswith("  - "):
            p.level = 2
            run = p.add_run()
            run.text = line[4:]
            set_font(run, size=Pt(12), color=TEXT_GRAY)
            p.space_before = Pt(2)
        elif line == "":
            p.space_before = Pt(8)
        else:
            run = p.add_run()
            run.text = line
            set_font(run, size=Pt(13), color=TEXT_DARK)
            p.space_before = Pt(4)
    return slide


def add_architecture_diagram(prs):
    """Create a visual architecture diagram slide with shapes."""
    slide = prs.slides.add_slide(BLANK_LAYOUT)

    # Title bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.33), Inches(1.1))
    bar.fill.solid()
    bar.fill.fore_color.rgb = PRIMARY
    bar.line.fill.background()
    txBox = slide.shapes.add_textbox(Inches(0.7), Inches(0.15), Inches(11), Inches(0.8))
    tf = txBox.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "System Architecture"
    set_font(run, size=Pt(24), bold=True, color=WHITE)

    # --- LAYER 1: Email Source (left) ---
    add_rounded_box(slide, Inches(0.3), Inches(1.6), Inches(1.8), Inches(0.9),
                    "Email Inbox\n(MS Graph)", fill_color=RGBColor(0x6B, 0x72, 0x80), font_size=Pt(10))

    # --- LAYER 2: AI Agent Pipeline (center) ---
    agents = [
        ("Email Intake\nAgent", Inches(2.6), RGBColor(0x1D, 0x4E, 0xD8)),
        ("Document\nUnderstanding", Inches(4.6), RGBColor(0x7C, 0x3A, 0xED)),
        ("Order\nExtraction", Inches(6.6), RGBColor(0x05, 0x96, 0x69)),
        ("Validation\nAgent", Inches(8.6), RGBColor(0xD9, 0x77, 0x06)),
    ]
    for name, left, color in agents:
        add_rounded_box(slide, left, Inches(1.6), Inches(1.7), Inches(0.9),
                        name, fill_color=color, font_size=Pt(9))

    # --- ROUTING OUTPUTS (row 2) ---
    add_rounded_box(slide, Inches(8.6), Inches(3.0), Inches(2.0), Inches(0.8),
                    "Order Creation\nAgent", fill_color=GREEN, font_size=Pt(9))
    add_rounded_box(slide, Inches(6.3), Inches(3.0), Inches(2.0), Inches(0.8),
                    "Communication\nAgent", fill_color=RGBColor(0xEA, 0x58, 0x0C), font_size=Pt(9))
    add_rounded_box(slide, Inches(4.0), Inches(3.0), Inches(2.0), Inches(0.8),
                    "HITL Review\nQueue", fill_color=RGBColor(0xBE, 0x12, 0x3C), font_size=Pt(9))

    # --- LAYER 3: Outputs (bottom) ---
    add_rounded_box(slide, Inches(8.8), Inches(4.2), Inches(1.8), Inches(0.7),
                    "Order Created", fill_color=GREEN, font_size=Pt(9))
    add_rounded_box(slide, Inches(6.5), Inches(4.2), Inches(1.8), Inches(0.7),
                    "Customer Email", fill_color=RGBColor(0xEA, 0x58, 0x0C), font_size=Pt(9))
    add_rounded_box(slide, Inches(4.2), Inches(4.2), Inches(1.8), Inches(0.7),
                    "Human Review", fill_color=RGBColor(0xBE, 0x12, 0x3C), font_size=Pt(9))

    # --- RIGHT SIDE: Infrastructure ---
    infra_top = Inches(1.4)
    add_rounded_box(slide, Inches(11.0), infra_top, Inches(2.0), Inches(0.6),
                    "PostgreSQL + pgvector", fill_color=RGBColor(0x33, 0x63, 0x91), font_size=Pt(9))
    add_rounded_box(slide, Inches(11.0), infra_top + Inches(0.75), Inches(2.0), Inches(0.6),
                    "Redis Cache", fill_color=RGBColor(0xDC, 0x26, 0x26), font_size=Pt(9))
    add_rounded_box(slide, Inches(11.0), infra_top + Inches(1.5), Inches(2.0), Inches(0.6),
                    "ElasticMQ (Queues)", fill_color=RGBColor(0x92, 0x33, 0xEA), font_size=Pt(9))
    add_rounded_box(slide, Inches(11.0), infra_top + Inches(2.25), Inches(2.0), Inches(0.6),
                    "MinIO (Storage)", fill_color=RGBColor(0xC0, 0x26, 0x56), font_size=Pt(9))
    add_rounded_box(slide, Inches(11.0), infra_top + Inches(3.0), Inches(2.0), Inches(0.6),
                    "OpenAI GPT-4o", fill_color=RGBColor(0x0E, 0x74, 0x90), font_size=Pt(9))

    # --- BOTTOM: Web Application ---
    add_rounded_box(slide, Inches(0.3), Inches(5.2), Inches(3.0), Inches(0.7),
                    "React Frontend (7 screens)", fill_color=RGBColor(0x1D, 0x4E, 0xD8), font_size=Pt(10))
    add_rounded_box(slide, Inches(3.6), Inches(5.2), Inches(3.0), Inches(0.7),
                    "FastAPI Backend (45 APIs)", fill_color=PRIMARY, font_size=Pt(10))
    add_rounded_box(slide, Inches(6.9), Inches(5.2), Inches(3.0), Inches(0.7),
                    "6 AI Agents (async)", fill_color=RGBColor(0x05, 0x96, 0x69), font_size=Pt(10))
    add_rounded_box(slide, Inches(10.2), Inches(5.2), Inches(2.8), Inches(0.7),
                    "Docker Compose", fill_color=RGBColor(0x64, 0x74, 0x8B), font_size=Pt(10))

    # --- Labels ---
    # "Confidence Routing" label
    lbl = slide.shapes.add_textbox(Inches(4.0), Inches(2.6), Inches(3), Inches(0.3))
    p = lbl.text_frame.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = "Confidence-Based Routing"
    set_font(run, size=Pt(9), bold=True, color=TEXT_GRAY)

    # ">=90% STP" label
    lbl2 = slide.shapes.add_textbox(Inches(8.8), Inches(2.6), Inches(2), Inches(0.3))
    p2 = lbl2.text_frame.paragraphs[0]
    run2 = p2.add_run()
    run2.text = ">=90% Auto-Process"
    set_font(run2, size=Pt(8), color=GREEN)

    # Infrastructure label
    lbl3 = slide.shapes.add_textbox(Inches(11.0), Inches(1.15), Inches(2), Inches(0.3))
    p3 = lbl3.text_frame.paragraphs[0]
    run3 = p3.add_run()
    run3.text = "Infrastructure"
    set_font(run3, size=Pt(10), bold=True, color=PRIMARY)

    # Processing time
    lbl4 = slide.shapes.add_textbox(Inches(0.3), Inches(6.2), Inches(5), Inches(0.4))
    p4 = lbl4.text_frame.paragraphs[0]
    run4 = p4.add_run()
    run4.text = "End-to-End Processing: ~9 seconds  |  Extraction Accuracy: 99.2%  |  197 Automated Tests"
    set_font(run4, size=Pt(10), bold=True, color=PRIMARY)

    return slide


def add_metrics_slide():
    """Visual metrics slide with KPI boxes."""
    slide = prs.slides.add_slide(BLANK_LAYOUT)

    # Title bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.33), Inches(1.1))
    bar.fill.solid()
    bar.fill.fore_color.rgb = PRIMARY
    bar.line.fill.background()
    txBox = slide.shapes.add_textbox(Inches(0.7), Inches(0.15), Inches(11), Inches(0.8))
    tf = txBox.text_frame
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "Implementation Metrics"
    set_font(run, size=Pt(24), bold=True, color=WHITE)

    # KPI boxes - Row 1
    metrics_row1 = [
        ("14", "Database\nTables"),
        ("45", "API\nEndpoints"),
        ("7", "Frontend\nScreens"),
        ("6", "AI\nAgents"),
        ("197", "Automated\nTests"),
    ]
    for i, (num, label) in enumerate(metrics_row1):
        left = Inches(0.5 + i * 2.5)
        # Number
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(1.5), Inches(2.2), Inches(1.6))
        box.fill.solid()
        box.fill.fore_color.rgb = LIGHT_GRAY
        box.line.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
        box.line.width = Pt(1)
        tf = box.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = num
        set_font(run, size=Pt(36), bold=True, color=PRIMARY)
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        run2 = p2.add_run()
        run2.text = label
        set_font(run2, size=Pt(11), color=TEXT_GRAY)

    # Row 2 - Detail boxes
    metrics_row2 = [
        ("49", "Configurable\nFields"),
        ("12", "Business\nRules"),
        ("4", "Email\nTemplates"),
        ("4", "User\nRoles"),
        ("9s", "E2E Processing\nTime"),
    ]
    for i, (num, label) in enumerate(metrics_row2):
        left = Inches(0.5 + i * 2.5)
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, Inches(3.5), Inches(2.2), Inches(1.6))
        box.fill.solid()
        box.fill.fore_color.rgb = LIGHT_GRAY
        box.line.color.rgb = RGBColor(0xE2, 0xE8, 0xF0)
        box.line.width = Pt(1)
        tf = box.text_frame
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = num
        set_font(run, size=Pt(36), bold=True, color=ACCENT)
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        run2 = p2.add_run()
        run2.text = label
        set_font(run2, size=Pt(11), color=TEXT_GRAY)

    # Bottom summary
    txBox2 = slide.shapes.add_textbox(Inches(0.5), Inches(5.5), Inches(12), Inches(1.2))
    tf2 = txBox2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    run = p.add_run()
    run.text = "Test Breakdown: "
    set_font(run, size=Pt(12), bold=True, color=PRIMARY)
    run2 = p.add_run()
    run2.text = "26 Playwright E2E  |  61 Field Validation  |  48 Admin Module  |  62 API Integration"
    set_font(run2, size=Pt(12), color=TEXT_GRAY)

    return slide


# ═══════════════════════════════════════════════════════════════════
# BUILD SLIDES
# ═══════════════════════════════════════════════════════════════════

# Slide 1: Title
add_exec_title_slide(
    "Order Intelligence Agent",
    "AI-Powered Order Intake & Automation for Transportation & Logistics\nPrepared by ideyaLabs"
)

# Slide 2: Problem & Opportunity
add_exec_content_slide("Business Challenge & Opportunity", [
    "## Current Pain Points",
    "- Manual order entry from emails takes 5-15 minutes per order",
    "- High error rates from manual data transcription (human fatigue)",
    "- No standardized process — inconsistent handling across agents",
    "- Customer follow-ups are reactive, not proactive",
    "- Limited visibility into pipeline status and throughput",
    "",
    "## Opportunity",
    "- 80-90% of manual data entry can be automated with AI",
    "- Real-time processing (9 seconds vs 5-15 minutes)",
    "- 24/7 automated operation — no staffing dependency",
    "- Consistent quality with configurable business rules",
    "- Complete audit trail for compliance and traceability",
])

# Slide 3: Solution Overview
add_exec_content_slide("Solution Overview", [
    "## Order Intelligence Agent Platform",
    "- Monitors email inbox for inbound shipment requests (24/7)",
    "- Extracts order data from emails + attachments using AI (GPT-4o)",
    "- Validates against 12 configurable business rules",
    "- Routes by confidence score: auto-process or human review",
    "- Communicates with customers for missing information (auto-follow-up)",
    "- Creates orders with Straight-Through Processing (STP)",
    "",
    "## Delivered Capabilities",
    "- Full web application for order management and operations",
    "- Role-based access: Readonly, Agent, Supervisor, Admin",
    "- Administration panel: field configs, rules, templates, users",
    "- Real-time dashboard with KPIs and trend analytics",
    "- Comprehensive audit logging with search and export",
])

# Slide 4: Architecture Diagram
add_architecture_diagram(prs)

# Slide 5: Tech Stack
add_exec_content_slide("Technology Stack", [
    "## Backend & AI",
    "- Python 3.12, FastAPI (async), SQLAlchemy 2.0, Pydantic v2",
    "- PostgreSQL 16 with pgvector extension",
    "- Redis 7 for caching, ElasticMQ for message queues",
    "- OpenAI GPT-4o (extraction) + GPT-4o-mini (classification)",
    "- pdfplumber + pytesseract for local OCR",
    "",
    "## Frontend",
    "- React 18 with TypeScript (strict mode)",
    "- Vite build tooling, Tailwind CSS v3",
    "- TanStack React Query v5, Recharts for data visualization",
    "",
    "## Integration & Infrastructure",
    "- Microsoft Graph API for email (inbound + outbound)",
    "- Docker Compose (8 containers, single-command deployment)",
    "- Adapter pattern: swap local services for AWS without code changes",
    "- JWT authentication, role-based access control",
])

# Slide 6: AI Agent Pipeline
add_exec_content_slide("AI Agent Pipeline — How It Works", [
    "## Processing Flow (Email → Order in 9 seconds)",
    "",
    "- 1. Email Intake Agent — polls inbox via MS Graph, classifies email type",
    "- 2. Document Understanding — extracts text from PDF/Excel/Word/images (OCR)",
    "- 3. Order Extraction — GPT-4o extracts 49 fields with confidence scores",
    "- 4. Validation Agent — checks mandatory fields, business rules, duplicates",
    "- 5. Routing Decision:",
    "  - Confidence >= 90%: Auto-process (STP)",
    "  - 80-90%: Human-in-the-Loop review queue",
    "  - Missing mandatory fields: Auto-email customer",
    "  - Hazmat orders: Always human review",
    "- 6. Order Creation — finalizes order + sends confirmation email",
    "",
    "## Proven Results",
    "- Test: Maple Leaf Foods shipment → 99.2% confidence → auto-created in 9 seconds",
    "- All 49 fields extracted correctly, confirmation email sent in thread",
])

# Slide 7: Web Application Features
add_exec_content_slide("Web Application — Key Screens", [
    "## Dashboard",
    "- Real-time KPIs: Total Orders, STP Rate, Avg E2E Time, Accuracy",
    "- Status distribution chart, pipeline breakdown, STP trend line",
    "",
    "## Order Management (Dynamic Form)",
    "- 4-step creation wizard, fields driven by admin configuration",
    "- Inline editing, status filters, confidence indicators",
    "",
    "## Operations",
    "- Review Queue: approve/reject with one click",
    "- Email Inbox: all processed emails with classification",
    "- Audit Logs: searchable, paginated, JSON diff, CSV export",
    "",
    "## Administration (5 tabs)",
    "- Field Configuration — 49 fields, toggle mandatory/conditional",
    "- Business Rules — 12 rules (date, enum, regex, required_if)",
    "- Email Templates — 4 types with variable substitution",
    "- User Management — create/edit users, assign roles",
    "- Thresholds — STP/HITL confidence boundaries",
])

# Slide 8: Implementation Metrics (visual KPI boxes)
add_metrics_slide()

# Slide 9: Security & Quality
add_exec_content_slide("Security, Quality & Testing", [
    "## Security",
    "- JWT Bearer token authentication with role-based access",
    "- 4-tier RBAC: Readonly < Agent < Supervisor < Admin",
    "- API endpoint-level authorization, UI navigation filtered by role",
    "",
    "## Audit & Compliance",
    "- Immutable audit trail — append-only order_history table",
    "- Every agent action logged with timestamp, actor, and context",
    "- Searchable audit logs with date filtering and CSV export",
    "",
    "## Testing (197 Automated Tests — All Passing)",
    "- 26 Playwright E2E: login, forms, RBAC, admin, order lifecycle",
    "- 61 Field Validation: every mandatory, enum, conditional, edge case",
    "- 48 Admin Module: CRUD for configs, rules, templates, users",
    "- 62 API Integration: auth, orders, queues, reports, conversations",
    "- Agent pipeline E2E: real email → extraction → order creation",
])

# Slide 10: Deployment
add_exec_content_slide("Deployment", [
    "## Current Status",
    "- Deployed on-premise: server 172.16.6.199",
    "- Single command deployment: docker compose up -d",
    "- 8 Docker containers, ~4GB RAM",
    "",
    "## External Dependencies (outbound only)",
    "- OpenAI API — for AI extraction and classification",
    "- Microsoft Graph API — for email inbox integration",
    "- No inbound ports required (pulls, doesn't listen)",
    "",
    "## Cloud Migration Path (When Ready)",
    "- Adapter pattern enables zero-code-change migration to AWS:",
    "  - ElasticMQ → Amazon SQS",
    "  - MinIO → Amazon S3",
    "  - Local OCR → AWS Textract",
    "  - OpenAI → AWS Bedrock (Claude)",
    "  - Local JWT → Amazon Cognito",
])

# Slide 11: Roadmap
add_exec_content_slide("Roadmap", [
    "## Phase 1 — Hardening (Next 2-4 weeks)",
    "- CI/CD pipeline with GitHub Actions",
    "- Database migrations with Alembic",
    "- Rate limiting, enhanced error handling",
    "",
    "## Phase 2 — AWS Cloud Deployment",
    "- CDK infrastructure-as-code",
    "- ECS Fargate, RDS, SQS, S3, Cognito",
    "- Production-grade scaling and monitoring",
    "",
    "## Phase 3 — Advanced Features",
    "- Real-time WebSocket notifications",
    "- pgvector semantic duplicate detection",
    "- Customer profile management",
    "",
    "## Phase 4 — Enterprise",
    "- Multi-tenant, SSO (SAML/OIDC)",
    "- CloudWatch dashboards, X-Ray tracing",
    "- Data retention policies",
])

# Slide 12: Thank You
add_exec_title_slide(
    "Thank You",
    "Order Intelligence Agent — Built by ideyaLabs\n\nDemo: https://172.16.6.199\nGitHub: github.com/mkbharath/BisonTransport"
)

# Save
output = "/Users/bharathm/BisonTransport/OIA_TechStack_Presentation.pptx"
prs.save(output)
print(f"Saved: {output}")
print(f"Total slides: {len(prs.slides)}")
