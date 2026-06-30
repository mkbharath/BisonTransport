"""Send a test shipment email to trigger the full agent pipeline."""
import os
import httpx

# MS Graph credentials from environment
tenant_id = os.environ.get("MSGRAPH_TENANT_ID", "")
client_id = os.environ.get("MSGRAPH_CLIENT_ID", "")
client_secret = os.environ.get("MSGRAPH_CLIENT_SECRET", "")
mailbox = os.environ.get("MSGRAPH_MAILBOX", "iltransport@ideyalabs.com")

if not all([tenant_id, client_id, client_secret]):
    print("ERROR: Set MSGRAPH_TENANT_ID, MSGRAPH_CLIENT_ID, MSGRAPH_CLIENT_SECRET env vars")
    print("  (or source .env.local before running)")
    exit(1)

# Get token
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
token_res = httpx.post(token_url, data={
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "https://graph.microsoft.com/.default",
    "grant_type": "client_credentials",
})
assert token_res.status_code == 200, f"Token failed: {token_res.text}"
token = token_res.json()["access_token"]
print(f"MS Graph token obtained: {token[:20]}...")

# Send a test order email
send_url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/sendMail"

email_body = """Hi Bison Transport Team,

We need to ship the following order:

Customer: Maple Leaf Foods
Contact: Sarah Johnson
Email: sarah.johnson@mapleleaf.com
Phone: +1-416-555-0192

PICKUP:
Location: Maple Leaf Foods - Distribution Center
Address: 6985 Financial Drive, Mississauga, ON L5N 0A1
Date: July 15, 2026
Time Window: 08:00 - 12:00

DELIVERY:
Location: Costco Wholesale #442
Address: 99 Glacier Drive, Moncton, NB E1E 4P2
Date: July 17, 2026
Time Window: 06:00 - 14:00

SHIPMENT:
Commodity: Frozen Chicken Products
Equipment: Reefer
Temperature: -18C to -22C
Weight: 42,000 lbs
Pallets: 22
Hazmat: No

Special Instructions: Temperature must remain below -18C at all times. Driver must have food safety certification.

Please confirm.

Thanks,
Sarah Johnson
Maple Leaf Foods
"""

message = {
    "message": {
        "subject": "New Shipment Request - Maple Leaf Foods - Jul 15 Pickup",
        "body": {"contentType": "Text", "content": email_body},
        "toRecipients": [{"emailAddress": {"address": mailbox}}],
    },
    "saveToSentItems": "false"
}

res = httpx.post(
    send_url,
    json=message,
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
)
print(f"Send email response: {res.status_code}")
if res.status_code == 202:
    print("Email sent successfully! Agent will pick it up on next poll cycle (60s).")
else:
    print(f"Error: {res.text}")
