"""Generate architecture diagram for BisonTransport / Order Intelligence Platform."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(22, 16))
ax.set_xlim(0, 22)
ax.set_ylim(0, 16)
ax.axis("off")
fig.patch.set_facecolor("white")

# Colors
NAVY = "#0f1b2d"
BLUE = "#1d4ed8"
GREEN = "#059669"
PURPLE = "#7c3aed"
ORANGE = "#ea580c"
RED = "#dc2626"
CYAN = "#0e7490"
GRAY = "#64748b"
AMBER = "#d97706"
TEAL = "#0d9488"
SLATE = "#334155"
INDIGO = "#6366f1"
AWS_ORANGE = "#ff9900"
AWS_BLUE = "#232f3e"
LIGHT_BG = "#f8fafc"


def box(x, y, w, h, text, color=BLUE, fontsize=8, textcolor="white", alpha=0.92):
    b = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.12",
        facecolor=color, edgecolor="none", alpha=alpha,
    )
    ax.add_patch(b)
    ax.text(
        x + w / 2, y + h / 2, text, ha="center", va="center",
        fontsize=fontsize, color=textcolor, fontweight="bold", linespacing=1.25,
    )


def section_bg(x, y, w, h, color, label="", label_color=SLATE):
    b = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.2",
        facecolor=color, edgecolor="#94a3b8", alpha=0.35, lw=1.2,
    )
    ax.add_patch(b)
    if label:
        ax.text(
            x + 0.3, y + h - 0.35, label, fontsize=9, color=label_color,
            fontweight="bold", va="top",
        )


def arrow(x1, y1, x2, y2, color=SLATE, style="-|>"):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle=style, color=color, lw=1.4),
    )


def darrow(x1, y1, x2, y2, color=SLATE):
    arrow(x1, y1, x2, y2, color=color)
    arrow(x2, y2, x1, y1, color=color)


# ═══════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════
ax.text(
    11, 15.5, "BisonTransport — Order Intelligence Platform Architecture",
    ha="center", fontsize=17, fontweight="bold", color=NAVY,
)
ax.text(
    11, 15.05, "Monorepo · Event-Driven AI Pipeline · Adapter Pattern (Local ↔ AWS)",
    ha="center", fontsize=10, color=GRAY,
)

# ═══════════════════════════════════════════════════════════════
# USERS & EXTERNAL
# ═══════════════════════════════════════════════════════════════
section_bg(0.3, 13.2, 21.4, 1.55, LIGHT_BG, "USERS & EXTERNAL SERVICES")

box(0.6, 13.55, 2.6, 0.85, "Email Customers\n(.eml / Outlook)", color=GRAY, fontsize=7.5)
box(3.5, 13.55, 2.6, 0.85, "Web Users\n(Agent / Admin)", color=SLATE, fontsize=7.5)
box(6.4, 13.55, 2.8, 0.85, "Microsoft Graph\n(Email Intake)", color=BLUE, fontsize=7.5)
box(9.5, 13.55, 2.8, 0.85, "Anthropic Claude\n/ OpenAI GPT-4o", color=GREEN, fontsize=7.5)
box(12.6, 13.55, 2.8, 0.85, "AWS Bedrock\n(Future)", color=AWS_ORANGE, fontsize=7.5)
box(15.7, 13.55, 2.5, 0.85, "AWS Textract\n(Future OCR)", color=AMBER, fontsize=7.5)
box(18.5, 13.55, 2.8, 0.85, "Playwright E2E\n+ Pytest Tests", color=INDIGO, fontsize=7.5)

# ═══════════════════════════════════════════════════════════════
# EDGE (AWS TARGET)
# ═══════════════════════════════════════════════════════════════
section_bg(0.3, 11.7, 6.5, 1.25, "#dbeafe", "EDGE (AWS)")

box(1.0, 12.0, 2.5, 0.65, "CloudFront CDN", color=BLUE, fontsize=8)
box(3.8, 12.0, 2.5, 0.65, "Route 53 DNS", color=BLUE, fontsize=8)

# AUTH
section_bg(7.2, 11.7, 4.2, 1.25, "#ede9fe", "AUTH")

box(7.7, 12.0, 3.2, 0.65, "JWT (Local) / Cognito (AWS)", color=PURPLE, fontsize=7.5)

# MONOREPO PACKAGES
section_bg(11.8, 11.7, 9.9, 1.25, "#f0fdf4", "MONOREPO PACKAGES")

box(12.2, 12.0, 2.2, 0.65, "frontend\nReact+Vite", color=BLUE, fontsize=7)
box(14.6, 12.0, 2.0, 0.65, "api\nFastAPI", color=CYAN, fontsize=7)
box(16.8, 12.0, 2.0, 0.65, "agents\n6 AI Agents", color=SLATE, fontsize=7)
box(19.0, 12.0, 2.4, 0.65, "shared\nPython+TS", color=TEAL, fontsize=7)

# ═══════════════════════════════════════════════════════════════
# RUNTIME — DOCKER COMPOSE / ECS
# ═══════════════════════════════════════════════════════════════
section_bg(0.3, 3.2, 21.4, 8.2, "#fff7ed", "RUNTIME — Docker Compose (Local) / ECS Fargate (AWS)")

# ALB
box(3.5, 10.5, 4.0, 0.65, "Nginx (Local) / ALB + WAF (AWS)", color=ORANGE, fontsize=7.5)

# Application services
section_bg(0.6, 7.8, 13.5, 2.5, "#dbeafe", "APPLICATION SERVICES")

box(1.0, 8.9, 3.2, 1.0, "Frontend Service\nReact 18 + Tailwind\nNginx :5173", color=BLUE, fontsize=7.5)
box(4.6, 8.9, 3.4, 1.0, "API Service\nFastAPI · 45+ Endpoints\n:8000 /api/v1/*", color=CYAN, fontsize=7.5)
box(8.4, 8.9, 5.3, 1.0, "Agent Runner\n6 concurrent asyncio tasks\nauto-restart on crash", color=SLATE, fontsize=7.5)

box(1.0, 8.0, 4.0, 0.6, "Pages: Dashboard, Orders, Inbox, Queue, Admin", color=INDIGO, fontsize=6.5)
box(5.3, 8.0, 4.2, 0.6, "Routers: orders, emails, queues, admin, reports", color=INDIGO, fontsize=6.5)
box(9.8, 8.0, 4.0, 0.6, "Shared adapters + SQLAlchemy models", color=INDIGO, fontsize=6.5)

# AI Agent Pipeline
section_bg(0.6, 4.5, 13.5, 3.0, "#ede9fe", "AI AGENT PIPELINE (SQS / ElasticMQ)")

agents = [
    ("Email\nIntake", "file watcher\n/ MS Graph", PURPLE),
    ("Document\nUnderstanding", "OCR + classify\nattachments", BLUE),
    ("Order\nExtraction", "LLM field\nextraction", GREEN),
    ("Validation", "rules engine\n+ confidence", AMBER),
    ("Communication", "customer\nemails", TEAL),
    ("Order\nCreation", "TMS order\ncreation", RED),
]
ax.text(1.0, 7.15, "Queue-driven pipeline:", fontsize=7.5, fontweight="bold", color=NAVY)

for i, (name, desc, color) in enumerate(agents):
    x = 0.8 + i * 2.15
    box(x, 5.5, 1.9, 0.85, name, color=color, fontsize=7)
    ax.text(x + 0.95, 5.2, desc, ha="center", fontsize=5.8, color=GRAY)

queues = [
    "→ document-processing",
    "→ extraction",
    "→ validation",
    "→ auto-process / hitl",
    "→ communication",
    "",
]
for i, q in enumerate(queues[:-1]):
    x = 2.65 + i * 2.15
    ax.text(x, 4.85, q, ha="center", fontsize=5.5, color=SLATE, style="italic")

ax.text(7.0, 4.55, "DLQs on all primary queues  ·  HITL queue for human review  ·  exception queue", fontsize=6.5, color=GRAY)

# Agent → queue arrows
for i in range(5):
    x1 = 1.75 + i * 2.15
    x2 = 2.65 + i * 2.15
    arrow(x1 + 0.95, 5.5, x2, 5.5, color=SLATE)

# DATA & MESSAGING
section_bg(14.5, 3.5, 7.0, 6.8, "#d1fae5", "DATA & MESSAGING")

box(14.8, 9.3, 3.0, 0.75, "PostgreSQL 16\n+ pgvector", color="#336391", fontsize=7.5)
box(18.1, 9.3, 3.0, 0.75, "Redis 7\nCache / Sessions", color=RED, fontsize=7.5)

box(14.8, 8.2, 3.0, 0.75, "ElasticMQ / SQS\n8 queues + DLQs", color=PURPLE, fontsize=7.5)
box(18.1, 8.2, 3.0, 0.75, "MinIO / S3\nattachments · exports", color="#c02656", fontsize=7.5)

box(14.8, 7.1, 3.0, 0.75, "Mailpit / SES\nOutbound email", color=TEAL, fontsize=7.5)
box(18.1, 7.1, 3.0, 0.75, "pytesseract /\nTextract OCR", color=AMBER, fontsize=7.5)

box(14.8, 6.0, 3.0, 0.75, "Local Events /\nEventBridge", color=ORANGE, fontsize=7.5)
box(18.1, 6.0, 3.0, 0.75, "CloudWatch\nLogs + Metrics", color=SLATE, fontsize=7.5)

box(14.8, 4.7, 6.3, 0.65, "Alembic Migrations  ·  Agent Execution Logs  ·  Audit Trail", color=INDIGO, fontsize=7)
box(14.8, 3.8, 6.3, 0.65, "Secrets Manager (AWS) / .env.local (Local)", color=AWS_BLUE, fontsize=7)

# ═══════════════════════════════════════════════════════════════
# ARROWS
# ═══════════════════════════════════════════════════════════════
arrow(4.8, 13.55, 2.6, 12.65, color=SLATE)       # Web users → edge
arrow(2.6, 12.0, 2.6, 11.55, color=BLUE)          # Edge → frontend
arrow(2.6, 10.5, 2.6, 9.9, color=BLUE)            # Nginx → frontend
arrow(6.2, 10.5, 6.3, 9.9, color=CYAN)            # Nginx → API
darrow(8.0, 9.4, 8.4, 9.4, color=SLATE)           # API ↔ agents
arrow(2.4, 13.55, 7.8, 9.9, color=PURPLE)          # Email → agents
arrow(11.0, 13.55, 10.5, 9.4, color=GREEN)         # LLM → agents
arrow(6.3, 8.9, 14.8, 9.65, color="#336391")      # API → Postgres
arrow(10.5, 8.5, 14.8, 8.55, color=PURPLE)        # Agents → queues
arrow(13.7, 8.5, 18.1, 8.55, color="#c02656")     # Agents → storage
arrow(13.7, 5.9, 18.1, 7.45, color=AMBER)         # Doc agent → OCR

# ═══════════════════════════════════════════════════════════════
# ADAPTER PATTERN
# ═══════════════════════════════════════════════════════════════
section_bg(0.3, 0.3, 21.4, 2.7, LIGHT_BG, "ADAPTER PATTERN — ADAPTER_MODE=local | aws")

ax.text(0.7, 2.35, "All infrastructure accessed via abstract interfaces in packages/shared/python/order_shared/adapters/", fontsize=7.5, color=GRAY)

adapters = [
    ("QueueAdapter", "ElasticMQ (local)", "Amazon SQS (aws)"),
    ("StorageAdapter", "MinIO (local)", "Amazon S3 (aws)"),
    ("EmailSender", "Mailpit / MS Graph", "Amazon SES (aws)"),
    ("LLMAdapter", "Anthropic / OpenAI", "AWS Bedrock (aws)"),
    ("OCRAdapter", "pytesseract (local)", "AWS Textract (aws)"),
    ("EventBusAdapter", "In-process (local)", "EventBridge (aws)"),
]
for i, (name, local_impl, aws_impl) in enumerate(adapters):
    col = i % 3
    row = i // 3
    x = 0.7 + col * 7.1
    y = 1.55 - row * 0.55
    ax.text(x, y, f"  {name}:", fontsize=7, fontweight="bold", color=NAVY)
    ax.text(x + 2.2, y, local_impl, fontsize=6.5, color=TEAL)
    ax.text(x + 4.5, y, "→", fontsize=6.5, color=GRAY)
    ax.text(x + 4.8, y, aws_impl, fontsize=6.5, color=AWS_ORANGE)

# Save
output_path = "/Users/bharathm/BisonTransport/Order_Intelligence_Architecture.png"
plt.tight_layout()
plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Architecture diagram saved: {output_path}")
