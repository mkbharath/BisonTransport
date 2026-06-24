"""Generate fresh test emails with unique Message-IDs for all demo scenarios.

Usage: python scripts/generate_test_emails.py
Outputs to: test-emails/fresh/
"""

import os
import uuid
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "test-emails" / "fresh"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def uid():
    return str(uuid.uuid4())[:8]


# --- Scenario 1: Perfect Order (all fields, should auto-create) ---
SCENARIO_1 = f"""From: logistics@saputo.com
To: orders@orderplatform.local
Subject: Transportation Order - Dairy Products to Vancouver
Date: Tue, 24 Jun 2026 10:00:00 -0400
Message-ID: <{uid()}@saputo.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

Hi Team,

Please arrange the following shipment:

Customer: Saputo Inc.
Contact: Marie Tremblay
Email: marie.tremblay@saputo.com
Phone: (514) 328-6662

PICKUP:
Location: Saputo Dairy Processing Plant
Address: 6869 Boulevard Metropolitain Est, Montreal, QC H1P 1X8, Canada
Date: July 10, 2026
Time: 05:00 - 08:00
Instructions: Dock 3, temperature log required at loading

DELIVERY:
Location: Save-On-Foods Distribution Centre
Address: 19855 92A Avenue, Langley, BC V1M 3B6, Canada
Date: July 14, 2026
Time: 06:00 - 10:00
Instructions: Report to receiving office first

SHIPMENT:
PO Number: SAP-2026-77123
Commodity: Fresh dairy products - cheese wheels and butter blocks
Freight Type: FTL
Weight: 38,000 lbs
Pallets: 22
Stackable: No

EQUIPMENT:
Type: Reefer
Temperature: 2C to 4C
Size: 53ft

Hazmat: No
Special Handling: Maintain cold chain at all times. Temperature monitoring required.

Please confirm.

Marie Tremblay
Saputo Logistics
"""

# --- Scenario 2: Missing Pickup Date ---
SCENARIO_2 = f"""From: shipping@krugerproducts.ca
To: orders@orderplatform.local
Subject: Shipment Request - Paper Products to Edmonton
Date: Tue, 24 Jun 2026 11:00:00 -0400
Message-ID: <{uid()}@krugerproducts.ca>
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

Hello,

We need to arrange a shipment from our Gatineau mill to Edmonton.

Customer: Kruger Products
Contact: David Wilson
Email: david.wilson@krugerproducts.ca
Phone: 819-555-0177

PICKUP:
Location: Kruger Products Mill
Address: 200 Rue de Carillon, Gatineau, QC J8P 3S3, Canada
Instructions: Use south gate entrance

DELIVERY:
Location: Superstore DC Edmonton
Address: 16940 114 Avenue NW, Edmonton, AB T5M 2Z8, Canada
Date: July 20, 2026
Time: 08:00 - 14:00

SHIPMENT:
PO: KP-2026-55890
Commodity: Bathroom tissue and paper towels (consumer packaged)
Freight Type: FTL
Weight: 28,000 lbs
Pallets: 26
Stackable: Yes

Equipment: Dry Van 53ft

Hazmat: No
Notes: Lightweight but high volume. Full trailer load by cube.

Thanks,
David Wilson
Kruger Products
"""

# --- Scenario 3: Missing Multiple Fields (delivery address + equipment type) ---
SCENARIO_3 = f"""From: dispatch@canfor.com
To: orders@orderplatform.local
Subject: Lumber shipment needed
Date: Tue, 24 Jun 2026 12:00:00 -0400
Message-ID: <{uid()}@canfor.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

Hi,

We have a lumber shipment that needs to move soon.

Customer: Canfor Corporation
Contact: Rob Fraser
Email: rob.fraser@canfor.com

PICKUP:
Location: Canfor Sawmill Prince George
Address: 2500 Boundary Road, Prince George, BC V2N 5S3, Canada
Date: July 12, 2026
Time: 07:00 - 11:00
Instructions: Scale at main gate, load at mill yard

DELIVERY:
(Destination TBD - either our Calgary or Winnipeg yard. Will confirm tomorrow.)

SHIPMENT:
Customer Order: CF-2026-41002
Commodity: Dimensional lumber - 2x4 and 2x6 SPF
Freight Type: FTL
Weight: 48,000 lbs
Pallets: 0 (bundled, no pallets)

Hazmat: No
Special Handling: Tarps required for weather protection. Secure with straps.

Will send delivery details and equipment needs shortly.

Rob Fraser
Canfor Logistics
"""

# --- Scenario 4: Ambiguous Commodity (should route to HITL ~80-85% confidence) ---
SCENARIO_4 = f"""From: shipping@teck.com
To: orders@orderplatform.local
Subject: Transport request - mining equipment
Date: Tue, 24 Jun 2026 13:00:00 -0400
Message-ID: <{uid()}@teck.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

Hello,

Need to move some equipment from our Trail operations to the Highland Valley site.

Customer: Teck Resources
Contact: James Nakamura
Email: james.nakamura@teck.com
Phone: 250-555-0188

From: Teck Trail Operations
Address: 8100 Trail Smelter Road, Trail, BC V1R 4L8, Canada
Pickup: July 16, 2026, flexible on time

To: Teck Highland Valley Copper
Address: Ashcroft Highway 97C, Logan Lake, BC V0K 1W0, Canada
Delivery: July 18, 2026

Cargo: assorted mining components and various replacement parts (mix of pumps, conveyor sections, and miscellaneous hardware)
Approximately 52,000 lbs
FTL

Hazmat: No
Notes: Some oversize pieces may require tarping. Call ahead for site access.

James
"""

# --- Scenario 5: Hazmat Order (should always route to HITL regardless of confidence) ---
SCENARIO_5 = f"""From: logistics@irvingoil.com
To: orders@orderplatform.local
Subject: HAZMAT - Fuel Additive Shipment
Date: Tue, 24 Jun 2026 14:00:00 -0400
Message-ID: <{uid()}@irvingoil.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

URGENT - HAZMAT SHIPMENT

Customer: Irving Oil
Contact: Patricia Drummond
Email: patricia.drummond@irvingoil.com
Phone: (506) 202-4000

PICKUP:
Location: Irving Oil Refinery
Address: 589 Grandview Avenue, Saint John, NB E2J 4M5, Canada
Date: July 11, 2026
Time: 06:00 - 09:00
Instructions: HAZMAT loading bay only. Driver requires TWIC card and safety orientation.

DELIVERY:
Location: Irving Oil Terminal Montreal
Address: 10500 Sherbrooke Street East, Montreal, QC H1B 1B3, Canada
Date: July 12, 2026
Time: 08:00 - 12:00
Instructions: Report to terminal control office. HAZMAT placards required.

SHIPMENT:
PO: IRV-2026-HAZ-0091
Commodity: Fuel additives - petroleum distillates
Freight Type: FTL
Weight: 44,000 lbs
Pallets: 20 (double-stacked IBC totes on pallets)
Stackable: No

EQUIPMENT:
Type: Tanker
Size: Standard

HAZMAT INFORMATION:
Hazmat: YES
UN Number: UN1268
Hazmat Class: Class 3 - Flammable Liquids

Special Handling: Full HAZMAT compliance required. Emergency response guide on board.
TWIC Card Required: Yes
Team Drive: No

Patricia Drummond
Irving Oil Logistics
"""

# --- Scenario 6: Duplicate (same customer, same pickup date, same delivery postal as Scenario 1) ---
SCENARIO_6 = f"""From: logistics@saputo.com
To: orders@orderplatform.local
Subject: RE: Transportation Order - Dairy Products to Vancouver (resending)
Date: Tue, 24 Jun 2026 15:00:00 -0400
Message-ID: <{uid()}@saputo.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

Hi again,

Not sure if my earlier email went through. Resending the order details:

Customer: Saputo Inc.
Contact: Marie Tremblay
Email: marie.tremblay@saputo.com
Phone: 514-328-6662

Pickup: Saputo Dairy Processing Plant, 6869 Boulevard Metropolitain Est, Montreal, QC H1P 1X8
Date: July 10, 2026

Delivery: Save-On-Foods DC, 19855 92A Avenue, Langley, BC V1M 3B6
Date: July 14, 2026

Commodity: Fresh dairy products (cheese and butter)
FTL, 38000 lbs, 22 pallets, Reefer (2-4C), 53ft

PO: SAP-2026-77123
Hazmat: No

Thanks,
Marie
"""

scenarios = {
    "scenario1-perfect-order.eml": SCENARIO_1,
    "scenario2-missing-pickup-date.eml": SCENARIO_2,
    "scenario3-missing-multiple-fields.eml": SCENARIO_3,
    "scenario4-ambiguous-commodity.eml": SCENARIO_4,
    "scenario5-hazmat-order.eml": SCENARIO_5,
    "scenario6-duplicate-order.eml": SCENARIO_6,
}


def main():
    for filename, content in scenarios.items():
        filepath = OUTPUT_DIR / filename
        filepath.write_text(content.strip() + "\n")
        print(f"  Created: {filepath}")

    print(f"\n{len(scenarios)} test emails generated in {OUTPUT_DIR}/")
    print("\nTo run all scenarios:")
    print("  1. Clear inbox: rm -f test-emails/inbox/*.eml")
    print("  2. Copy all:    cp test-emails/fresh/*.eml test-emails/inbox/")
    print("  3. Wait 2 min and check results in frontend + MailHog")
    print("\nExpected outcomes:")
    print("  Scenario 1: Auto-process or HITL (confidence ~95%+)")
    print("  Scenario 2: Missing-info email for 'Pickup Date'")
    print("  Scenario 3: Missing-info email for 'Delivery Address' + 'Equipment Type'")
    print("  Scenario 4: HITL queue (ambiguous commodity, ~80-85%)")
    print("  Scenario 5: HITL queue (Hazmat = always HITL)")
    print("  Scenario 6: Duplicate detected (same customer+date+postal as Scenario 1)")


if __name__ == "__main__":
    main()
