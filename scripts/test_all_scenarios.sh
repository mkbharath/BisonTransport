#!/bin/bash
set -e

API_URL="http://localhost:8000/api/v1"
MAILPIT_URL="http://localhost:8025"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }

echo "=============================================="
echo " ORDER INTELLIGENCE PLATFORM - FULL TEST RUN"
echo "=============================================="
echo ""

# --- RESET ---
log "Resetting database..."
docker compose exec postgres psql -U orderuser -d orderdb -c "DELETE FROM agent_execution_logs; DELETE FROM audit_logs; DELETE FROM order_history; DELETE FROM validation_results; DELETE FROM conversation_messages; UPDATE emails SET conversation_id = NULL; DELETE FROM conversations; DELETE FROM email_attachments; UPDATE orders SET source_email_id = NULL; DELETE FROM emails; DELETE FROM orders;" > /dev/null 2>&1
success "Database cleared"

log "Clearing inbox and Mailpit..."
rm -f test-emails/inbox/*.eml
curl -s -X DELETE "$MAILPIT_URL/api/v1/messages" > /dev/null 2>&1
success "Inbox and Mailpit cleared"

log "Generating fresh test emails..."
python3 scripts/generate_test_emails.py > /dev/null 2>&1
success "6 test emails generated with unique Message-IDs"

log "Restarting agents..."
docker compose restart agents > /dev/null 2>&1
sleep 5
success "Agents restarted"

# --- AUTH ---
TOKEN=$(curl -s -X POST "$API_URL/auth/login" -H "Content-Type: application/json" -d '{"email":"agent@test.com","password":"agent123"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

echo ""
echo "=============================================="
echo " SCENARIO 1: Perfect Order (Saputo - Dairy)"
echo " Expected: auto-create or HITL (conf >= 90%)"
echo "=============================================="
cp test-emails/fresh/scenario1-perfect-order.eml test-emails/inbox/
sleep 45
log "Result:"
curl -s "$API_URL/orders" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for o in data['data']:
    if 'Saputo' in (o.get('customer_name') or ''):
        print(f'  Order: {o[\"order_number\"]}')
        print(f'  Status: {o[\"status\"]}')
        print(f'  Confidence: {o.get(\"overall_confidence_score\")}%')
        print(f'  Customer: {o.get(\"customer_name\")}')
        print(f'  Pickup: {o.get(\"pickup_date\")}')
        break
else:
    print('  Order not found yet (may need more time)')
"
echo ""

echo "=============================================="
echo " SCENARIO 2: Missing Pickup Date (Kruger)"
echo " Expected: awaiting_customer + email sent"
echo "=============================================="
cp test-emails/fresh/scenario2-missing-pickup-date.eml test-emails/inbox/
sleep 45
log "Result:"
curl -s "$API_URL/orders" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for o in data['data']:
    if 'Kruger' in (o.get('customer_name') or ''):
        print(f'  Order: {o[\"order_number\"]}')
        print(f'  Status: {o[\"status\"]}')
        print(f'  Confidence: {o.get(\"overall_confidence_score\")}%')
        print(f'  Pickup Date: {o.get(\"pickup_date\") or \"MISSING (expected)\"}')
        break
else:
    print('  Order not found yet')
"
echo ""

echo "=============================================="
echo " SCENARIO 3: Missing Multiple Fields (Canfor)"
echo " Expected: awaiting_customer + email listing"
echo "  delivery address + equipment type"
echo "=============================================="
cp test-emails/fresh/scenario3-missing-multiple-fields.eml test-emails/inbox/
sleep 45
log "Result:"
curl -s "$API_URL/orders" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for o in data['data']:
    if 'Canfor' in (o.get('customer_name') or ''):
        print(f'  Order: {o[\"order_number\"]}')
        print(f'  Status: {o[\"status\"]}')
        print(f'  Confidence: {o.get(\"overall_confidence_score\")}%')
        print(f'  Equipment: {o.get(\"equipment_type\") or \"MISSING (expected)\"}')
        break
else:
    print('  Order not found yet')
"
echo ""

echo "=============================================="
echo " SCENARIO 4: Ambiguous Commodity (Teck)"
echo " Expected: pending_review (HITL queue)"
echo "=============================================="
cp test-emails/fresh/scenario4-ambiguous-commodity.eml test-emails/inbox/
sleep 45
log "Result:"
curl -s "$API_URL/orders" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for o in data['data']:
    if 'Teck' in (o.get('customer_name') or ''):
        print(f'  Order: {o[\"order_number\"]}')
        print(f'  Status: {o[\"status\"]}')
        print(f'  Confidence: {o.get(\"overall_confidence_score\")}%')
        print(f'  Commodity: {o.get(\"commodity\") or \"-\"}')
        break
else:
    print('  Order not found yet')
"
echo ""

echo "=============================================="
echo " SCENARIO 5: HAZMAT Order (Irving Oil)"
echo " Expected: pending_review (always HITL)"
echo "=============================================="
cp test-emails/fresh/scenario5-hazmat-order.eml test-emails/inbox/
sleep 45
log "Result:"
curl -s "$API_URL/orders" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for o in data['data']:
    if 'Irving' in (o.get('customer_name') or ''):
        print(f'  Order: {o[\"order_number\"]}')
        print(f'  Status: {o[\"status\"]}')
        print(f'  Confidence: {o.get(\"overall_confidence_score\")}%')
        print(f'  Hazmat: {o.get(\"hazmat_indicator\")}')
        print(f'  UN Number: {o.get(\"hazmat_un_number\") or \"-\"}')
        break
else:
    print('  Order not found yet')
"
echo ""

echo "=============================================="
echo " SCENARIO 6: Duplicate Order (Saputo again)"
echo " Expected: pending_review (duplicate detected)"
echo "=============================================="
cp test-emails/fresh/scenario6-duplicate-order.eml test-emails/inbox/
sleep 45
log "Result:"
curl -s "$API_URL/orders" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
saputo_orders = [o for o in data['data'] if 'Saputo' in (o.get('customer_name') or '')]
print(f'  Saputo orders found: {len(saputo_orders)}')
for o in saputo_orders:
    print(f'    {o[\"order_number\"]} | {o[\"status\"]} | conf={o.get(\"overall_confidence_score\")}')
"
echo ""

echo "=============================================="
echo " SCENARIO 7: Customer Response (Kruger reply)"
echo " Expected: Kruger order updated with pickup"
echo "  date and re-validated"
echo "=============================================="
cp test-emails/fresh/scenario7-customer-reply-pickup-date.eml test-emails/inbox/
sleep 60
log "Result:"
curl -s "$API_URL/orders" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for o in data['data']:
    if 'Kruger' in (o.get('customer_name') or ''):
        print(f'  Order: {o[\"order_number\"]}')
        print(f'  Status: {o[\"status\"]}')
        print(f'  Pickup Date: {o.get(\"pickup_date\") or \"still missing\"}')
        break
"
echo ""

echo "=============================================="
echo " SUMMARY"
echo "=============================================="
echo ""
log "Dashboard KPIs:"
curl -s "$API_URL/reports/dashboard" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'  Total Orders:       {d[\"total_orders\"]}')
print(f'  Pending:            {d[\"pending\"]}')
print(f'  Awaiting Customer:  {d[\"awaiting_customer\"]}')
print(f'  Auto-Processed:     {d[\"auto_processed\"]}')
print(f'  STP Rate:           {d[\"stp_rate\"]}%')
print(f'  HITL Queue:         {d[\"hitl_queue_depth\"]}')
print(f'  Completed:          {d[\"completed\"]}')
print(f'  Failed:             {d[\"failed\"]}')
"
echo ""
log "Emails sent (check http://localhost:8025):"
curl -s "$MAILPIT_URL/api/v1/messages" | python3 -c "
import sys, json
data = json.load(sys.stdin)
msgs = data.get('messages', [])
print(f'  Total outbound emails: {len(msgs)}')
for m in msgs[:5]:
    to = m.get('To', [{}])[0].get('Address', '?')
    subj = m.get('Subject', '?')
    print(f'    To: {to} | {subj[:60]}')
" 2>/dev/null || echo "  (check Mailpit manually at http://localhost:8025)"
echo ""
echo "=============================================="
log "All scenarios complete!"
log "Frontend: http://localhost:5173"
log "Mailpit:  http://localhost:8025"
echo "=============================================="
