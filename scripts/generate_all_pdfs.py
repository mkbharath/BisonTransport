"""Generate PDF attachments for all test scenarios."""

from fpdf import FPDF
import os

OUTPUT_DIR = "test-emails/fixtures"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def create_pdf(filename, sections):
    """Create a PDF with given sections."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    for section in sections:
        if section["type"] == "header":
            pdf.set_font("Helvetica", "B", 18)
            pdf.cell(0, 15, section["text"], new_x="LMARGIN", new_y="NEXT", align="C")
        elif section["type"] == "subheader":
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 8, section["text"], new_x="LMARGIN", new_y="NEXT", align="C")
        elif section["type"] == "section_title":
            pdf.ln(5)
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, section["text"], new_x="LMARGIN", new_y="NEXT")
        elif section["type"] == "field":
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(55, 7, section["label"], 0)
            pdf.cell(0, 7, section["value"], new_x="LMARGIN", new_y="NEXT")
        elif section["type"] == "separator":
            pdf.ln(3)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
        elif section["type"] == "note":
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(0, 7, section["text"])
        elif section["type"] == "footer":
            pdf.ln(10)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            pdf.set_font("Helvetica", "I", 9)
            pdf.cell(0, 6, section["text"], new_x="LMARGIN", new_y="NEXT", align="C")
        elif section["type"] == "spacer":
            pdf.ln(5)

    filepath = os.path.join(OUTPUT_DIR, filename)
    pdf.output(filepath)
    print(f"  Created: {filepath}")


# --- Scenario 1: Perfect Order (all fields) ---
create_pdf("scenario1-perfect-order.pdf", [
    {"type": "header", "text": "RATE CONFIRMATION"},
    {"type": "subheader", "text": "Document #: RC-2026-0728-001 | Date: June 27, 2026"},
    {"type": "separator"},
    {"type": "section_title", "text": "CUSTOMER INFORMATION"},
    {"type": "field", "label": "Customer:", "value": "SteelMax Industries"},
    {"type": "field", "label": "Contact:", "value": "Priya Sharma"},
    {"type": "field", "label": "Email:", "value": "bharathm@ideyalabs.com"},
    {"type": "field", "label": "Phone:", "value": "+91 9988776655"},
    {"type": "section_title", "text": "PICKUP DETAILS"},
    {"type": "field", "label": "Location:", "value": "SteelMax Manufacturing Plant"},
    {"type": "field", "label": "Address:", "value": "45 MIDC Industrial Area, Pune, MH 411026, India"},
    {"type": "field", "label": "Date:", "value": "July 28, 2026"},
    {"type": "field", "label": "Time Window:", "value": "07:00 - 10:00"},
    {"type": "field", "label": "Instructions:", "value": "Weigh bridge entry, report to dispatch office"},
    {"type": "section_title", "text": "DELIVERY DETAILS"},
    {"type": "field", "label": "Location:", "value": "SteelMax Mumbai Warehouse"},
    {"type": "field", "label": "Address:", "value": "12 Taloja Industrial Estate, Navi Mumbai, MH 410208, India"},
    {"type": "field", "label": "Date:", "value": "July 29, 2026"},
    {"type": "field", "label": "Time Window:", "value": "09:00 - 13:00"},
    {"type": "field", "label": "Instructions:", "value": "Bay 4, crane unloading available"},
    {"type": "section_title", "text": "SHIPMENT DETAILS"},
    {"type": "field", "label": "PO Number:", "value": "SM-2026-5501"},
    {"type": "field", "label": "Commodity:", "value": "Carbon steel pipes and fittings"},
    {"type": "field", "label": "Freight Type:", "value": "FTL (Full Truck Load)"},
    {"type": "field", "label": "Weight:", "value": "44,000 lbs"},
    {"type": "field", "label": "Pallets:", "value": "20"},
    {"type": "field", "label": "Stackable:", "value": "No"},
    {"type": "section_title", "text": "TRANSPORTATION"},
    {"type": "field", "label": "Equipment:", "value": "Flatbed"},
    {"type": "field", "label": "Truck Size:", "value": "40 ft"},
    {"type": "field", "label": "Hazmat:", "value": "No"},
    {"type": "section_title", "text": "SPECIAL INSTRUCTIONS"},
    {"type": "note", "text": "Secure with steel straps. Cover with tarpaulin if rain expected. Heavy load - ensure vehicle rated for 44,000+ lbs."},
    {"type": "footer", "text": "SteelMax Industries | Pune, India | logistics@steelmax.com"},
])

# --- Scenario 2: Missing Pickup Date ---
create_pdf("scenario2-missing-pickup-date.pdf", [
    {"type": "header", "text": "SHIPPING ORDER"},
    {"type": "subheader", "text": "Order #: TV-2026-8812 | Date: June 27, 2026"},
    {"type": "separator"},
    {"type": "section_title", "text": "CUSTOMER"},
    {"type": "field", "label": "Customer:", "value": "TechVista Solutions"},
    {"type": "field", "label": "Contact:", "value": "Amit Patel"},
    {"type": "field", "label": "Email:", "value": "bharathm@ideyalabs.com"},
    {"type": "field", "label": "Phone:", "value": "+91 8877665544"},
    {"type": "section_title", "text": "PICKUP"},
    {"type": "field", "label": "Location:", "value": "TechVista Warehouse"},
    {"type": "field", "label": "Address:", "value": "78 Peenya Industrial Area, Bangalore, KA 560058, India"},
    {"type": "field", "label": "Date:", "value": "(TO BE CONFIRMED)"},
    {"type": "field", "label": "Instructions:", "value": "Loading dock at rear entrance"},
    {"type": "section_title", "text": "DELIVERY"},
    {"type": "field", "label": "Location:", "value": "TechVista Delhi Office"},
    {"type": "field", "label": "Address:", "value": "55 Sector 62, Noida, UP 201301, India"},
    {"type": "field", "label": "Date:", "value": "August 5, 2026"},
    {"type": "field", "label": "Time:", "value": "10:00 - 14:00"},
    {"type": "section_title", "text": "SHIPMENT"},
    {"type": "field", "label": "Commodity:", "value": "Server racks, UPS systems, networking equipment"},
    {"type": "field", "label": "Freight Type:", "value": "FTL"},
    {"type": "field", "label": "Weight:", "value": "18,000 lbs"},
    {"type": "field", "label": "Pallets:", "value": "10"},
    {"type": "field", "label": "Equipment:", "value": "Dry Van"},
    {"type": "field", "label": "Hazmat:", "value": "No"},
    {"type": "section_title", "text": "NOTES"},
    {"type": "note", "text": "Fragile electronic equipment. Handle with extreme care. Anti-static packaging on all server components."},
    {"type": "footer", "text": "TechVista Solutions | Bangalore, India"},
])

# --- Scenario 3: Missing Multiple Fields ---
create_pdf("scenario3-missing-multiple-fields.pdf", [
    {"type": "header", "text": "TRANSPORT REQUEST"},
    {"type": "subheader", "text": "Date: June 27, 2026"},
    {"type": "separator"},
    {"type": "section_title", "text": "SHIPPER"},
    {"type": "field", "label": "Customer:", "value": "GreenLeaf Organics"},
    {"type": "field", "label": "Contact:", "value": "Meera Nair"},
    {"type": "field", "label": "Email:", "value": "bharathm@ideyalabs.com"},
    {"type": "section_title", "text": "ORIGIN"},
    {"type": "field", "label": "Location:", "value": "GreenLeaf Farm"},
    {"type": "field", "label": "Address:", "value": "Village Kothrud, Taluka Mulshi, Pune, MH 412115, India"},
    {"type": "field", "label": "Pickup Date:", "value": "August 1, 2026"},
    {"type": "section_title", "text": "DESTINATION"},
    {"type": "field", "label": "Location:", "value": "(TO BE CONFIRMED)"},
    {"type": "field", "label": "Address:", "value": "(TO BE CONFIRMED)"},
    {"type": "field", "label": "Delivery Date:", "value": "(TO BE CONFIRMED)"},
    {"type": "section_title", "text": "CARGO"},
    {"type": "field", "label": "Commodity:", "value": "Organic produce - fruits and vegetables"},
    {"type": "field", "label": "Weight:", "value": "8,000 lbs"},
    {"type": "field", "label": "Hazmat:", "value": "No"},
    {"type": "spacer"},
    {"type": "note", "text": "NOTE: Delivery details, freight type, and equipment requirements will be confirmed separately."},
    {"type": "footer", "text": "GreenLeaf Organics | Pune, India"},
])

# --- Scenario 4: Ambiguous Commodity ---
create_pdf("scenario4-ambiguous-commodity.pdf", [
    {"type": "header", "text": "MOVE ORDER"},
    {"type": "subheader", "text": "Warehouse Relocation | Date: June 27, 2026"},
    {"type": "separator"},
    {"type": "section_title", "text": "COMPANY"},
    {"type": "field", "label": "Customer:", "value": "Apex Logistics"},
    {"type": "field", "label": "Contact:", "value": "Rahul Verma"},
    {"type": "field", "label": "Email:", "value": "bharathm@ideyalabs.com"},
    {"type": "field", "label": "Phone:", "value": "+91 7766554433"},
    {"type": "section_title", "text": "FROM"},
    {"type": "field", "label": "Location:", "value": "Apex Old Warehouse"},
    {"type": "field", "label": "Address:", "value": "Plot 23, Jigani Industrial Area, Bangalore, KA 560105, India"},
    {"type": "field", "label": "Date:", "value": "August 10, 2026"},
    {"type": "field", "label": "Time:", "value": "08:00 - 12:00"},
    {"type": "section_title", "text": "TO"},
    {"type": "field", "label": "Location:", "value": "Apex New Facility"},
    {"type": "field", "label": "Address:", "value": "Survey 45, Bommasandra, Bangalore, KA 560099, India"},
    {"type": "field", "label": "Date:", "value": "August 11, 2026"},
    {"type": "field", "label": "Time:", "value": "09:00 - 15:00"},
    {"type": "section_title", "text": "CARGO DETAILS"},
    {"type": "field", "label": "Description:", "value": "Assorted warehouse items - old furniture, spare parts,"},
    {"type": "field", "label": "", "value": "random equipment, boxes of miscellaneous stuff"},
    {"type": "field", "label": "Freight:", "value": "FTL"},
    {"type": "field", "label": "Weight:", "value": "Approx 25,000 lbs"},
    {"type": "field", "label": "Pallets:", "value": "14 (estimated)"},
    {"type": "field", "label": "Hazmat:", "value": "No"},
    {"type": "spacer"},
    {"type": "note", "text": "Mixed load with various sizes. Some items bulky and irregularly shaped. Equipment type not determined yet."},
    {"type": "footer", "text": "Apex Logistics | Bangalore, India"},
])

# --- Scenario 5: HAZMAT Order ---
create_pdf("scenario5-hazmat-order.pdf", [
    {"type": "header", "text": "HAZMAT SHIPPING ORDER"},
    {"type": "subheader", "text": "DANGEROUS GOODS | Document #: CS-2026-HAZ-042"},
    {"type": "separator"},
    {"type": "section_title", "text": "SHIPPER INFORMATION"},
    {"type": "field", "label": "Customer:", "value": "ChemSafe Industries"},
    {"type": "field", "label": "Contact:", "value": "Dr. Suresh Kumar"},
    {"type": "field", "label": "Email:", "value": "bharathm@ideyalabs.com"},
    {"type": "field", "label": "Phone:", "value": "+91 9900887766"},
    {"type": "section_title", "text": "PICKUP"},
    {"type": "field", "label": "Location:", "value": "ChemSafe Manufacturing Unit"},
    {"type": "field", "label": "Address:", "value": "15 Chemical Zone, Ambernath MIDC, Thane, MH 421501, India"},
    {"type": "field", "label": "Date:", "value": "August 8, 2026"},
    {"type": "field", "label": "Time:", "value": "06:00 - 08:00"},
    {"type": "field", "label": "Instructions:", "value": "HAZMAT loading bay only. Safety certification required."},
    {"type": "section_title", "text": "DELIVERY"},
    {"type": "field", "label": "Location:", "value": "ChemSafe Storage Facility"},
    {"type": "field", "label": "Address:", "value": "201 Pharma City, Visakhapatnam, AP 531019, India"},
    {"type": "field", "label": "Date:", "value": "August 10, 2026"},
    {"type": "field", "label": "Time:", "value": "10:00 - 14:00"},
    {"type": "field", "label": "Instructions:", "value": "Hazmat receiving dock. Safety officer must be present."},
    {"type": "section_title", "text": "SHIPMENT"},
    {"type": "field", "label": "Commodity:", "value": "Industrial solvents and chemical reagents"},
    {"type": "field", "label": "Freight Type:", "value": "FTL"},
    {"type": "field", "label": "Weight:", "value": "35,000 lbs"},
    {"type": "field", "label": "Pallets:", "value": "16"},
    {"type": "field", "label": "Equipment:", "value": "Tanker"},
    {"type": "section_title", "text": "HAZARDOUS MATERIALS"},
    {"type": "field", "label": "Hazmat:", "value": "YES"},
    {"type": "field", "label": "UN Number:", "value": "UN1993"},
    {"type": "field", "label": "Hazmat Class:", "value": "Class 3 - Flammable Liquids"},
    {"type": "field", "label": "TWIC Required:", "value": "Yes"},
    {"type": "field", "label": "Emergency Kit:", "value": "Required on board"},
    {"type": "footer", "text": "ChemSafe Industries | HAZMAT Division | Emergency: +91 9900887766"},
])

# --- Scenario 6: Duplicate (same as Scenario 1 with slight rewording) ---
create_pdf("scenario6-duplicate-order.pdf", [
    {"type": "header", "text": "SHIPPING CONFIRMATION"},
    {"type": "subheader", "text": "Re-submission | Date: June 27, 2026"},
    {"type": "separator"},
    {"type": "section_title", "text": "CUSTOMER"},
    {"type": "field", "label": "Customer:", "value": "SteelMax Industries"},
    {"type": "field", "label": "Contact:", "value": "Priya Sharma"},
    {"type": "field", "label": "Email:", "value": "bharathm@ideyalabs.com"},
    {"type": "section_title", "text": "PICKUP"},
    {"type": "field", "label": "Location:", "value": "SteelMax Plant, Pune"},
    {"type": "field", "label": "Address:", "value": "45 MIDC Industrial Area, Pune, MH 411026"},
    {"type": "field", "label": "Date:", "value": "July 28, 2026"},
    {"type": "section_title", "text": "DELIVERY"},
    {"type": "field", "label": "Location:", "value": "SteelMax Warehouse, Mumbai"},
    {"type": "field", "label": "Address:", "value": "12 Taloja Industrial Estate, Navi Mumbai, MH 410208"},
    {"type": "field", "label": "Date:", "value": "July 29, 2026"},
    {"type": "section_title", "text": "CARGO"},
    {"type": "field", "label": "Commodity:", "value": "Carbon steel pipes and fittings"},
    {"type": "field", "label": "Freight:", "value": "FTL"},
    {"type": "field", "label": "Weight:", "value": "44,000 lbs"},
    {"type": "field", "label": "Pallets:", "value": "20"},
    {"type": "field", "label": "Equipment:", "value": "Flatbed"},
    {"type": "field", "label": "PO:", "value": "SM-2026-5501"},
    {"type": "field", "label": "Hazmat:", "value": "No"},
    {"type": "spacer"},
    {"type": "note", "text": "This is a re-submission of our earlier order. Please confirm if already received."},
    {"type": "footer", "text": "SteelMax Industries | Pune, India"},
])

print(f"\nAll 6 PDF scenarios generated in {OUTPUT_DIR}/")
print("\nTo test: attach each PDF to an email sent to iltransport@ideyalabs.com")
print("Email body can be: 'Please process the attached shipment order.'")
