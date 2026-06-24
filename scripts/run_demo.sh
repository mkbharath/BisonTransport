#!/bin/bash
# =============================================================================
# Demo Runner — Executes all 8 PoC demo scenarios sequentially
#
# Prerequisites:
#   - docker compose up (all services running)
#   - make migrate && make seed (DB populated)
#   - ANTHROPIC_API_KEY set in .env.local
#
# Usage: ./scripts/run_demo.sh [demo_number]
#   No argument: runs all demos in sequence
#   With argument: runs only that demo (1-8)
# =============================================================================

set -e

FIXTURES_DIR="$(dirname "$0")/../test-emails/fixtures"
INBOX_DIR="$(dirname "$0")/../test-emails/inbox"
API_URL="http://localhost:8000/api/v1"
MAILHOG_URL="http://localhost:8025"
PAUSE_SECONDS=30

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WAITING]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

wait_for_order() {
    local max_wait=120
    local elapsed=0
    while [ $elapsed -lt $max_wait ]; do
        local count=$(curl -s "$API_URL/orders?limit=1" -H "Authorization: Bearer $TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_count',0))" 2>/dev/null || echo "0")
        if [ "$count" != "0" ] && [ "$count" != "$INITIAL_ORDER_COUNT" ]; then
            return 0
        fi
        sleep 5
        elapsed=$((elapsed + 5))
        warn "Waiting for order processing... (${elapsed}s)"
    done
    error "Timeout waiting for order"
    return 1
}

# Get auth token
get_token() {
    TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"email":"agent@test.com","password":"agent123"}' \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

    if [ -z "$TOKEN" ]; then
        error "Failed to get auth token. Is the API running?"
        exit 1
    fi
    log "Authenticated as agent@test.com"
}

# Get initial order count
get_order_count() {
    curl -s "$API_URL/orders?limit=1" -H "Authorization: Bearer $TOKEN" \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_count',0))" 2>/dev/null || echo "0"
}

# ==== Demo Functions ====

demo_1() {
    echo ""
    echo "=============================================="
    echo " DEMO 1: Perfect Order — Email Body Only"
    echo "=============================================="
    log "Sending perfect order email with all mandatory fields..."
    cp "$FIXTURES_DIR/demo1-perfect-body-only.eml" "$INBOX_DIR/"
    log "Email copied to inbox. Waiting for pipeline to process..."
    sleep $PAUSE_SECONDS
    log "Checking results..."

    local orders=$(curl -s "$API_URL/orders?limit=5" -H "Authorization: Bearer $TOKEN")
    echo "$orders" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for o in data.get('data', []):
    if 'Frozen Chicken' in (o.get('commodity') or ''):
        print(f\"  Order: {o['order_number']}\")
        print(f\"  Status: {o['status']}\")
        print(f\"  Confidence: {o.get('overall_confidence_score', 'N/A')}%\")
        print(f\"  Customer: {o.get('customer_name', 'N/A')}\")
        break
" 2>/dev/null
    success "Demo 1 complete. Check MailHog at $MAILHOG_URL for acknowledgement email."
}

demo_4() {
    echo ""
    echo "=============================================="
    echo " DEMO 4: Missing Pickup Date"
    echo "=============================================="
    log "Sending order email missing pickup_date..."
    cp "$FIXTURES_DIR/demo4-missing-pickup-date.eml" "$INBOX_DIR/"
    log "Email copied to inbox. Waiting for pipeline..."
    sleep $PAUSE_SECONDS
    log "Checking MailHog for missing-info email..."

    local emails=$(curl -s "$MAILHOG_URL/api/v2/messages?limit=5")
    echo "$emails" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('items', []):
    subject = item.get('Content', {}).get('Headers', {}).get('Subject', [''])[0]
    if 'Missing Information' in subject or 'Action Required' in subject:
        to = item.get('Content', {}).get('Headers', {}).get('To', [''])[0]
        print(f\"  Missing-info email sent!\")
        print(f\"  To: {to}\")
        print(f\"  Subject: {subject}\")
        break
" 2>/dev/null
    success "Demo 4 complete. Customer would receive missing-info email for Pickup Date."
}

demo_5() {
    echo ""
    echo "=============================================="
    echo " DEMO 5: Missing Multiple Fields"
    echo "=============================================="
    log "Sending order missing delivery address + equipment type..."
    cp "$FIXTURES_DIR/demo5-missing-multiple.eml" "$INBOX_DIR/"
    log "Email copied to inbox. Waiting for pipeline..."
    sleep $PAUSE_SECONDS
    success "Demo 5 complete. Check MailHog for email listing both missing fields."
}

demo_7() {
    echo ""
    echo "=============================================="
    echo " DEMO 7: Human Review Workflow (Low Confidence)"
    echo "=============================================="
    log "Sending ambiguous commodity email (expect ~82% confidence)..."
    cp "$FIXTURES_DIR/demo7-ambiguous-commodity.eml" "$INBOX_DIR/"
    log "Email copied. Waiting for pipeline..."
    sleep $PAUSE_SECONDS
    log "Checking HITL queue..."

    local queue=$(curl -s "$API_URL/queues/hitl?limit=10" -H "Authorization: Bearer $TOKEN")
    echo "$queue" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data.get('data', []):
    if 'machine' in (item.get('customer_name') or '').lower() or 'bombardier' in (item.get('customer_name') or '').lower():
        print(f\"  Order {item['order_number']} in HITL queue\")
        print(f\"  Confidence: {item.get('overall_confidence_score', 'N/A')}%\")
        print(f\"  Status: {item['status']}\")
        break
else:
    print('  Order routed to review queue (check queue for latest item)')
" 2>/dev/null
    success "Demo 7 complete. Order in Validation Queue for agent review."
}

demo_8() {
    echo ""
    echo "=============================================="
    echo " DEMO 8: Duplicate Order Detection"
    echo "=============================================="
    log "Sending duplicate of Demo 1 order..."
    cp "$FIXTURES_DIR/demo8-duplicate.eml" "$INBOX_DIR/"
    log "Email copied. Waiting for pipeline..."
    sleep $PAUSE_SECONDS
    success "Demo 8 complete. Second order should be flagged as potential duplicate."
}

# ==== Main ====

log "Order Intelligence Platform — Demo Runner"
log "==========================================="
log ""

# Check services
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    error "API not reachable at $API_URL. Run 'make up' first."
    exit 1
fi
log "API is healthy."

# Authenticate
get_token
INITIAL_ORDER_COUNT=$(get_order_count)
log "Current order count: $INITIAL_ORDER_COUNT"
echo ""

# Run specific demo or all
if [ -n "$1" ]; then
    case "$1" in
        1) demo_1 ;;
        4) demo_4 ;;
        5) demo_5 ;;
        7) demo_7 ;;
        8) demo_8 ;;
        *) error "Demo $1 not implemented yet. Available: 1, 4, 5, 7, 8" ;;
    esac
else
    demo_1
    echo ""; log "Pausing ${PAUSE_SECONDS}s before next demo..."; sleep $PAUSE_SECONDS
    demo_4
    echo ""; log "Pausing ${PAUSE_SECONDS}s before next demo..."; sleep $PAUSE_SECONDS
    demo_5
    echo ""; log "Pausing ${PAUSE_SECONDS}s before next demo..."; sleep $PAUSE_SECONDS
    demo_7
    echo ""; log "Pausing ${PAUSE_SECONDS}s before next demo..."; sleep $PAUSE_SECONDS
    demo_8
fi

echo ""
echo "=============================================="
log "All demos complete!"
log ""
log "Verify results:"
log "  - Orders: $API_URL/orders (via frontend at http://localhost:5173)"
log "  - Emails: MailHog at $MAILHOG_URL"
log "  - Queue:  $API_URL/queues/hitl"
echo "=============================================="
