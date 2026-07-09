"""Send test emails for all scenarios to iltransport@ideyalabs.com."""
import os
import httpx
import time

tenant_id = os.environ.get("MSGRAPH_TENANT_ID", "")
client_id = os.environ.get("MSGRAPH_CLIENT_ID", "")
client_secret = os.environ.get("MSGRAPH_CLIENT_SECRET", "")
mailbox = os.environ.get("MSGRAPH_MAILBOX", "iltransport@ideyalabs.com")

if not all([tenant_id, client_id, client_secret]):
    print("ERROR: Set MSGRAPH env vars or source .env.local")
    exit(1)

# Get token
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
token_res = httpx.post(token_url, data={
    "client_id": client_id,
    "client_secret": client_secret,
    "scope": "https://graph.microsoft.com/.default",
    "grant_type": "client_credentials",
})
token = token_res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
send_url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/sendMail"


def send_email(subject, body):
    message = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": mailbox}}],
        },
        "saveToSentItems": "false"
    }
    res = httpx.post(send_url, json=message, headers=headers)
    status = "OK" if res.status_code == 202 else f"FAIL({res.status_code})"
    print(f"  [{status}] {subject}")
    time.sleep(2)  # Avoid throttling


print("Sending test scenarios to", mailbox)
print("=" * 60)

# Scenario 1: Perfect Order (should auto-process at 90%+ confidence)
print("\n1. Perfect Order (all fields present)")
send_email(
    "Shipment Request - TechVista Solutions - Jul 25",
    """Hi Bison Transport,

Please arrange the following shipment:

Customer: TechVista Solutions Inc.
Contact: Michael Chen
Email: m.chen@techvista.ca
Phone: +1-604-555-0188

PICKUP:
Location: TechVista Distribution Center
Address: 4521 Boundary Road, Burnaby, BC V5R 2N8
Date: July 25, 2026
Time: 08:00 - 12:00

DELIVERY:
Location: Best Buy DC - Ontario
Address: 2155 Dunwin Drive, Mississauga, ON L5L 1X2
Date: July 28, 2026
Time: 06:00 - 18:00

SHIPMENT:
Commodity: Consumer Electronics - TV displays
Equipment: Dry Van
Weight: 38,500 lbs
Pallets: 20
Freight Type: FTL
Hazmat: No

Special Instructions: Fragile cargo - no double stacking. Driver must have clean dry trailer.

Thanks,
Michael Chen
TechVista Solutions"""
)

# Scenario 2: Missing Fields (should trigger communication agent)
print("\n2. Missing Fields (no delivery info)")
send_email(
    "Need a truck - SteelMax Industries",
    """Hello,

We need to ship some steel beams from our yard.

Customer: SteelMax Industries
Contact: Robert Kraft
Email: r.kraft@steelmax.com
Phone: 416-555-0234

Pickup from: SteelMax Fabrication Yard
Address: 89 Industrial Parkway, Hamilton, ON L8W 3B2
Pickup Date: July 28, 2026

Commodity: Structural Steel I-Beams
Weight: 44,000 lbs
Equipment: Flatbed
26 pieces, strapped and blocked

Please advise on delivery details - we'll confirm destination shortly.

Robert"""
)

# Scenario 3: Hazmat Order (should route to HITL regardless of confidence)
print("\n3. Hazmat Order (should go to HITL)")
send_email(
    "HAZMAT Shipment Request - ChemFlow Corp",
    """Attention Bison Transport Dispatch,

We require transport of hazardous materials:

Customer: ChemFlow Corporation
Contact: Dr. Sarah Williams
Email: s.williams@chemflow.ca
Phone: +1-905-555-0199

PICKUP:
Location: ChemFlow Manufacturing Plant
Address: 1200 Chemical Lane, Sarnia, ON N7T 7H5
Date: July 30, 2026
Time: 06:00 - 10:00

DELIVERY:
Location: Dow Chemical Receiving
Address: 5555 Petrochemical Drive, Fort Saskatchewan, AB T8L 4G2
Date: August 2, 2026
Time: 08:00 - 16:00

SHIPMENT DETAILS:
Commodity: Industrial Solvents - Toluene
Equipment: Tanker
Weight: 42,000 lbs
Freight Type: FTL
HAZMAT: YES
UN Number: UN1294
Hazmat Class: 3 (Flammable Liquid)
Packing Group: II

Special Instructions: Driver must have HAZMAT endorsement and WHMIS training. No smoking within 50ft. Emergency contact: 1-800-CHEMFLOW

Dr. Sarah Williams
Safety & Logistics Manager
ChemFlow Corporation"""
)

# Scenario 4: Reefer with Temperature Requirements
print("\n4. Reefer Order (temperature-controlled)")
send_email(
    "Refrigerated Transport Needed - Northern Seafood",
    """Hi there,

We need a reefer truck for fresh seafood transport:

Company: Northern Seafood Distributors
Contact: James MacLeod
Email: j.macleod@northernseafood.ca
Phone: 902-555-0167

FROM:
Location: Northern Seafood Processing Plant
Address: 45 Harbour Drive, Lunenburg, NS B0J 2C0
Date: July 22, 2026
Time Window: 05:00 - 07:00 (early morning load)

TO:
Location: Metro Inc. Distribution Center
Address: 11011 Boulevard Maurice-Duplessis, Montreal, QC H1C 1V6
Date: July 24, 2026
Time: 04:00 - 10:00

Commodity: Fresh Atlantic Lobster & Shrimp
Equipment: Reefer
Temperature: Must maintain 2°C to 4°C at all times
Weight: 28,000 lbs
Pallets: 14
Type: FTL
Hazmat: No

CRITICAL: Temperature must not exceed 4°C. Product spoils above 5°C.
Driver must record temperature every 2 hours.

Thanks,
James MacLeod"""
)

# Scenario 5: LTL / Partial Load
print("\n5. LTL Partial Load")
send_email(
    "Partial Load Request - Cascade Paper",
    """Hello Bison team,

We have a partial load that needs to move:

Customer: Cascade Paper Products
Contact: Lisa Wong
Email: l.wong@cascadepaper.com
Phone: 604-555-0145

Pickup: Cascade Mill #3
Address: 777 River Road, Prince George, BC V2L 5R5
Date: July 26, 2026

Delivery: Staples Canada Warehouse
Address: 500 Consumers Road, North York, ON M2J 1P8
Date: July 30, 2026

Shipment: Copy Paper & Cardstock
6 pallets, 8,500 lbs total
Equipment: Dry Van
Freight: LTL
No hazmat

Standard shrink-wrapped pallets, 48x40 standard size.

Lisa Wong
Logistics Coordinator"""
)

# Scenario 6: Duplicate (same customer + same pickup date as Scenario 1)
print("\n6. Duplicate Order (same customer, same date as #1)")
send_email(
    "URGENT - TechVista Solutions - Jul 25 Shipment",
    """Hi,

Following up on our shipment request - please confirm:

Customer: TechVista Solutions Inc.
Contact: Michael Chen
Email: m.chen@techvista.ca
Phone: +1-604-555-0188

Pickup: TechVista Distribution Center
4521 Boundary Road, Burnaby, BC V5R 2N8
Date: July 25, 2026

Delivery: Best Buy DC Ontario
2155 Dunwin Drive, Mississauga, ON L5L 1X2
Date: July 28, 2026

Electronics - TV displays, 20 pallets, 38,500 lbs
Dry Van, FTL, No hazmat

Please confirm ASAP.

Michael"""
)

print("\n" + "=" * 60)
print("All 6 scenarios sent!")
print("""
Expected routing:
  1. Perfect Order      → Auto-process (>=90% confidence, no issues)
  2. Missing Fields     → Communication Agent (emails customer for delivery details)
  3. Hazmat             → HITL Review Queue (hazmat always requires human review)
  4. Reefer             → Auto-process (all fields present, temp specified)
  5. LTL Partial        → Auto-process or HITL (depends on confidence)
  6. Duplicate          → HITL Review Queue (same customer + pickup date as #1)

Check results in 1-2 minutes at the Orders page.
""")
