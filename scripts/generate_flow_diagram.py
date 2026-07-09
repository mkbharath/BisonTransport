"""Generate a clean, numbered flow diagram for Order Intelligence Agent."""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(1, 1, figsize=(18, 22))
ax.set_xlim(0, 18)
ax.set_ylim(0, 22)
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


def box(x, y, w, h, text, color=BLUE, fontsize=9):
    b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                       facecolor=color, edgecolor="none", alpha=0.9)
    ax.add_patch(b)
    ax.text(x + w/2, y + h/2, text, ha="center", va="center",
            fontsize=fontsize, color="white", fontweight="bold",
            linespacing=1.3)


def diamond(x, y, w, h, text, color=AMBER):
    cx, cy = x + w/2, y + h/2
    pts = [[cx, y+h], [x+w, cy], [cx, y], [x, cy]]
    d = plt.Polygon(pts, facecolor=color, edgecolor="none", alpha=0.9)
    ax.add_patch(d)
    ax.text(cx, cy, text, ha="center", va="center",
            fontsize=8, color="white", fontweight="bold", linespacing=1.2)


def arrow(x1, y1, x2, y2, num=None, label=""):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.8,
                               connectionstyle="arc3,rad=0"))
    if num:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx - 0.3, my, str(num), fontsize=8, color=BLUE,
                fontweight="bold", ha="center", va="center",
                bbox=dict(boxstyle="circle", facecolor="#e0f2fe", edgecolor=BLUE, lw=0.8, pad=0.2))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        offset = 0.25 if x1 == x2 else 0.2
        ax.text(mx + 0.3, my + offset, label, fontsize=7, color=GRAY, ha="left", style="italic")


# ═══════════════════════════════════════════════════════════════
# TITLE
# ═══════════════════════════════════════════════════════════════
ax.text(9, 21.3, "Order Intelligence Agent — Complete Processing Flow",
        ha="center", fontsize=16, fontweight="bold", color=NAVY)

# ═══════════════════════════════════════════════════════════════
# STEP 1: Email Received
# ═══════════════════════════════════════════════════════════════
box(6, 19.8, 6, 0.8, "EMAIL RECEIVED\n(iltransport@ideyalabs.com)", color=GRAY, fontsize=9)

# ═══════════════════════════════════════════════════════════════
# STEP 2: Email Intake Agent
# ═══════════════════════════════════════════════════════════════
arrow(9, 19.8, 9, 19.0, num=1)
box(6, 18.2, 6, 0.8, "EMAIL INTAKE AGENT\nClassify: new_order / reply / other", color=BLUE, fontsize=9)

# ═══════════════════════════════════════════════════════════════
# STEP 3: Document Understanding
# ═══════════════════════════════════════════════════════════════
arrow(9, 18.2, 9, 17.4, num=2)
box(6, 16.6, 6, 0.8, "DOCUMENT UNDERSTANDING AGENT\nOCR: PDF / Excel / Word / Image", color=PURPLE, fontsize=9)

# ═══════════════════════════════════════════════════════════════
# STEP 4: Order Extraction
# ═══════════════════════════════════════════════════════════════
arrow(9, 16.6, 9, 15.8, num=3)
box(6, 15.0, 6, 0.8, "ORDER EXTRACTION AGENT (GPT-4o)\nExtract 49 fields + confidence scores", color=GREEN, fontsize=9)

# ═══════════════════════════════════════════════════════════════
# STEP 5: Validation Agent
# ═══════════════════════════════════════════════════════════════
arrow(9, 15.0, 9, 14.2, num=4)
box(6, 13.4, 6, 0.8, "VALIDATION AGENT\nBusiness rules + Duplicate check", color=ORANGE, fontsize=9)

# ═══════════════════════════════════════════════════════════════
# DECISION 1: Hazmat?
# ═══════════════════════════════════════════════════════════════
arrow(9, 13.4, 9, 12.6, num=5)
diamond(7.5, 11.6, 3, 1.0, "HAZMAT?", color=RED)

# YES → HITL
arrow(10.5, 12.1, 14.5, 12.1, label="YES")
box(14.5, 11.7, 3, 0.8, "HITL QUEUE\n(Hazmat Review)", color=RED, fontsize=8)

# NO → next decision
arrow(9, 11.6, 9, 10.8, label="NO")

# ═══════════════════════════════════════════════════════════════
# DECISION 2: Duplicate?
# ═══════════════════════════════════════════════════════════════
diamond(7.5, 9.8, 3, 1.0, "DUPLICATE?", color=PURPLE)

# YES → HITL
arrow(10.5, 10.3, 14.5, 10.3, label="YES")
box(14.5, 9.9, 3, 0.8, "HITL QUEUE\n(Duplicate Review)", color=PURPLE, fontsize=8)

# NO → next decision
arrow(9, 9.8, 9, 9.0, label="NO")

# ═══════════════════════════════════════════════════════════════
# DECISION 3: Missing Mandatory Fields?
# ═══════════════════════════════════════════════════════════════
diamond(7.5, 8.0, 3, 1.0, "MISSING\nFIELDS?", color=ORANGE)

# YES → Communication
arrow(10.5, 8.5, 14.5, 8.5, label="YES")
box(14.5, 8.1, 3, 0.8, "COMMUNICATION AGENT\nAuto-email customer", color=ORANGE, fontsize=8)

# NO → next decision
arrow(9, 8.0, 9, 7.2, label="NO")

# ═══════════════════════════════════════════════════════════════
# DECISION 4: Confidence >= Threshold?
# ═══════════════════════════════════════════════════════════════
diamond(7.5, 6.2, 3, 1.0, "CONFIDENCE\n>= 90%?", color=GREEN)

# YES → Auto Process
arrow(7.5, 6.7, 3.5, 6.7, label="YES")
box(0.5, 6.3, 3, 0.8, "ORDER CREATION AGENT\nAuto-Process (STP)", color=GREEN, fontsize=8)

# NO → HITL (80-90% range)
arrow(10.5, 6.7, 14.5, 6.7, label="NO (80-90%)")
box(14.5, 6.3, 3, 0.8, "HITL QUEUE\n(Confidence Review)", color=AMBER, fontsize=8)

# ═══════════════════════════════════════════════════════════════
# OUTCOMES
# ═══════════════════════════════════════════════════════════════

# Auto-process → Order Created
arrow(2, 6.3, 2, 5.3, num=6)
box(0.5, 4.5, 3, 0.8, "ORDER CREATED\n+ Confirmation Email Sent", color="#047857", fontsize=8)

# Communication → Awaiting Customer
arrow(16, 8.1, 16, 7.1, num=7)
box(14.5, 6.3, 3, 0.8, "HITL QUEUE\n(Confidence Review)", color=AMBER, fontsize=8)

# Show awaiting customer below communication
arrow(16, 8.1, 16, 5.3)
box(14.5, 4.5, 3, 0.8, "AWAITING CUSTOMER\nWaiting for reply", color=AMBER, fontsize=8)

# Customer replies → re-validate
arrow(14.5, 4.9, 12.5, 4.9, num=8, label="Customer replies")
box(9.5, 4.5, 3, 0.8, "MERGE DATA\n+ Re-validate", color=TEAL, fontsize=8)
arrow(11, 5.3, 9, 8.0)  # back to validation decisions

# HITL Approve → Order Created
arrow(16, 9.9, 16, 5.3)

# Follow-up
box(14.5, 3.2, 3, 0.7, "FOLLOW-UP (24h)\nEscalate after 2 attempts", color=GRAY, fontsize=7)
arrow(16, 4.5, 16, 3.9, num=9)

# ═══════════════════════════════════════════════════════════════
# SCENARIO LEGEND
# ═══════════════════════════════════════════════════════════════
legend_y = 2.2
ax.text(1, legend_y + 0.3, "SCENARIOS:", fontsize=10, fontweight="bold", color=NAVY)

scenarios = [
    (GREEN, "Scenario 1: Perfect Order (all fields, >=90%) -> Auto-process -> Order Created"),
    (ORANGE, "Scenario 2: Missing Fields (no delivery) -> Communication Agent -> Email Customer"),
    (RED, "Scenario 3: Hazmat Order -> Always HITL (regardless of confidence)"),
    (GREEN, "Scenario 4: Reefer (all fields + temperature) -> Auto-process"),
    (AMBER, "Scenario 5: LTL/Partial (depends on confidence) -> Auto or HITL"),
    (PURPLE, "Scenario 6: Duplicate (same customer + date) -> HITL Duplicate Review"),
]

for i, (color, text) in enumerate(scenarios):
    y = legend_y - 0.45 * (i + 1)
    dot = plt.Circle((1.2, y + 0.05), 0.12, color=color)
    ax.add_patch(dot)
    ax.text(1.6, y, text, fontsize=8, color=NAVY, va="center")

# Save
output_path = "/Users/bharathm/BisonTransport/Order_Intelligence_Flow_Diagram.png"
plt.tight_layout()
plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
plt.close()
print(f"Flow diagram saved: {output_path}")
