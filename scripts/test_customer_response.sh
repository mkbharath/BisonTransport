#!/bin/bash
set -e

echo "=== STEP 0: Full clean reset ==="
docker compose exec postgres psql -U orderuser -d orderdb -c "DELETE FROM agent_execution_logs; DELETE FROM audit_logs; DELETE FROM order_history; DELETE FROM validation_results; DELETE FROM conversation_messages; UPDATE emails SET conversation_id = NULL; DELETE FROM conversations; DELETE FROM email_attachments; UPDATE orders SET source_email_id = NULL; DELETE FROM emails; DELETE FROM orders;"
rm -f test-emails/inbox/*.eml
curl -s -X DELETE http://localhost:8025/api/v1/messages > /dev/null 2>&1

echo "=== STEP 1: Generate fresh emails ==="
python3 scripts/generate_test_emails.py

echo "=== STEP 2: Restart agents ==="
docker compose restart agents
sleep 5

echo "=== STEP 3: Send scenario 2 (missing pickup date) ==="
cp test-emails/fresh/scenario2-missing-pickup-date.eml test-emails/inbox/
echo "Waiting 60s for processing..."
sleep 60

echo "=== STEP 4: Check order status ==="
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d '{"email":"agent@test.com","password":"agent123"}' | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
curl -s http://localhost:8000/api/v1/orders -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -20

echo ""
echo "=== STEP 5: Send customer reply with pickup date ==="
cp test-emails/fresh/scenario7-customer-reply-pickup-date.eml test-emails/inbox/
echo "Waiting 60s for processing..."
sleep 60

echo "=== STEP 6: Check order status after reply ==="
curl -s http://localhost:8000/api/v1/orders -H "Authorization: Bearer $TOKEN" | python3 -m json.tool | head -20

echo ""
echo "=== STEP 7: Agent logs ==="
docker compose logs agents --since 3m | grep -i "customer\|merged\|classified\|confidence\|routed"

echo ""
echo "=== DONE ==="
