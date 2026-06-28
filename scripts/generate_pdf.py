"""Generate a sample Rate Confirmation PDF for testing."""

from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)

# Header
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 15, "RATE CONFIRMATION", ln=True, align="C")
pdf.set_font("Helvetica", "", 10)
pdf.cell(0, 8, "Document #: RC-2026-0815-001", ln=True, align="C")
pdf.cell(0, 8, "Date: June 27, 2026", ln=True, align="C")
pdf.ln(10)

# Line separator
pdf.set_draw_color(0, 0, 0)
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(5)

# Customer Info
pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 8, "CUSTOMER INFORMATION", ln=True)
pdf.set_font("Helvetica", "", 11)
pdf.cell(50, 7, "Customer:", 0)
pdf.cell(0, 7, "Pacific Logistics Inc.", ln=True)
pdf.cell(50, 7, "Contact:", 0)
pdf.cell(0, 7, "Bharath M", ln=True)
pdf.cell(50, 7, "Email:", 0)
pdf.cell(0, 7, "bharathm@ideyalabs.com", ln=True)
pdf.cell(50, 7, "Phone:", 0)
pdf.cell(0, 7, "+91 9876543210", ln=True)
pdf.ln(8)

# Pickup Info
pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 8, "PICKUP DETAILS", ln=True)
pdf.set_font("Helvetica", "", 11)
pdf.cell(50, 7, "Location:", 0)
pdf.cell(0, 7, "Pacific Warehouse", ln=True)
pdf.cell(50, 7, "Address:", 0)
pdf.cell(0, 7, "200 Harbor Blvd, Chennai, TN 600001, India", ln=True)
pdf.cell(50, 7, "Date:", 0)
pdf.cell(0, 7, "August 15, 2026", ln=True)
pdf.cell(50, 7, "Time Window:", 0)
pdf.cell(0, 7, "08:00 - 11:00", ln=True)
pdf.cell(50, 7, "Instructions:", 0)
pdf.cell(0, 7, "Report to gate security, dock assignment at office", ln=True)
pdf.ln(8)

# Delivery Info
pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 8, "DELIVERY DETAILS", ln=True)
pdf.set_font("Helvetica", "", 11)
pdf.cell(50, 7, "Location:", 0)
pdf.cell(0, 7, "Pacific Hub Delhi", ln=True)
pdf.cell(50, 7, "Address:", 0)
pdf.cell(0, 7, "50 NH-44, Gurgaon, HR 122001, India", ln=True)
pdf.cell(50, 7, "Date:", 0)
pdf.cell(0, 7, "August 18, 2026", ln=True)
pdf.cell(50, 7, "Time Window:", 0)
pdf.cell(0, 7, "10:00 - 14:00", ln=True)
pdf.cell(50, 7, "Instructions:", 0)
pdf.cell(0, 7, "Bay 6, call 30 min before arrival", ln=True)
pdf.ln(8)

# Shipment Details
pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 8, "SHIPMENT DETAILS", ln=True)
pdf.set_font("Helvetica", "", 11)
pdf.cell(50, 7, "PO Number:", 0)
pdf.cell(0, 7, "PL-2026-7788", ln=True)
pdf.cell(50, 7, "Commodity:", 0)
pdf.cell(0, 7, "Auto spare parts and accessories", ln=True)
pdf.cell(50, 7, "Freight Type:", 0)
pdf.cell(0, 7, "FTL (Full Truck Load)", ln=True)
pdf.cell(50, 7, "Weight:", 0)
pdf.cell(0, 7, "22,000 lbs", ln=True)
pdf.cell(50, 7, "Pallets:", 0)
pdf.cell(0, 7, "14", ln=True)
pdf.cell(50, 7, "Stackable:", 0)
pdf.cell(0, 7, "No", ln=True)
pdf.ln(8)

# Transportation
pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 8, "TRANSPORTATION", ln=True)
pdf.set_font("Helvetica", "", 11)
pdf.cell(50, 7, "Equipment:", 0)
pdf.cell(0, 7, "Dry Van", ln=True)
pdf.cell(50, 7, "Truck Size:", 0)
pdf.cell(0, 7, "53 ft", ln=True)
pdf.cell(50, 7, "Hazmat:", 0)
pdf.cell(0, 7, "No", ln=True)
pdf.ln(8)

# Special Instructions
pdf.set_font("Helvetica", "B", 12)
pdf.cell(0, 8, "SPECIAL INSTRUCTIONS", ln=True)
pdf.set_font("Helvetica", "", 11)
pdf.multi_cell(0, 7, "Fragile items on 2 pallets - mark as top load only. Do not stack. Handle with care during loading and unloading.")
pdf.ln(10)

# Footer
pdf.line(10, pdf.get_y(), 200, pdf.get_y())
pdf.ln(5)
pdf.set_font("Helvetica", "I", 9)
pdf.cell(0, 6, "This rate confirmation is valid for 48 hours from the date of issue.", ln=True, align="C")
pdf.cell(0, 6, "Pacific Logistics Inc. | www.pacificlogistics.com | orders@pacificlogistics.com", ln=True, align="C")

# Save
output_path = "test-emails/fixtures/rate-confirmation-pacific-logistics.pdf"
pdf.output(output_path)
print(f"PDF created: {output_path}")
