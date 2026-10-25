import fitz  # PyMuPDF
from pathlib import Path

output_dir = Path(__file__).resolve().parent
output_dir.mkdir(parents=True, exist_ok=True)
pdf_path = output_dir / "Heat_Exchanger_E204_Inspection_Report.pdf"

doc = fitz.open()

# ==================== PAGE 1 ====================
page1 = doc.new_page(width=595, height=842)  # A4 size

# Header banner
rect = fitz.Rect(40, 40, 555, 95)
page1.draw_rect(rect, color=(0.14, 0.38, 0.92), fill=(0.14, 0.38, 0.92))
page1.insert_text(fitz.Point(55, 65), "SOVEREIGN INDUSTRIAL ENGINEERING AUDIT", fontname="helv", fontsize=11, color=(1, 1, 1))
page1.insert_text(fitz.Point(55, 85), "EQUIPMENT INTEGRITY & INSPECTION REPORT", fontname="helv", fontsize=15, color=(1, 1, 1))

# Metadata block
y = 125
page1.insert_text(fitz.Point(40, y), "DOCUMENT NO: MRPL-INSP-2025-E204", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))
page1.insert_text(fitz.Point(340, y), "INSPECTION DATE: October 14, 2025", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))

y += 20
page1.insert_text(fitz.Point(40, y), "FACILITY: MRPL Refining Complex - CDU-1", fontname="helv", fontsize=10, color=(0.2, 0.2, 0.2))
page1.insert_text(fitz.Point(340, y), "NEXT INSPECTION: October 2026 (Due to wear)", fontname="helv", fontsize=10, color=(0.8, 0.1, 0.1))

# Section 1
y += 35
page1.insert_text(fitz.Point(40, y), "1.0 GENERAL EQUIPMENT SPECIFICATION", fontname="helv", fontsize=12, color=(0.1, 0.1, 0.1))
page1.draw_line(fitz.Point(40, y + 4), fitz.Point(555, y + 4), color=(0.8, 0.8, 0.8), width=1)

y += 25
specs = [
    ("Equipment Tag:", "E-204 (Crude Pre-flash Column Overhead Condenser)"),
    ("Equipment Type:", "TEMA Class R - Shell and Tube Heat Exchanger (AES Type)"),
    ("Design Code:", "ASME Section VIII Division 1 (2019 Edition) / TEMA Class R"),
    ("Inspection Standard:", "API 510 (Pressure Vessel Inspection) & API 579-1 / ASME FFS-1"),
    ("Design Pressure:", "Shell Side: 15.5 bar (g) | Tube Side: 18.0 bar (g)"),
    ("Design Temperature:", "Shell Side: 185 deg C | Tube Side: 110 deg C"),
    ("Operating Fluid:", "Shell: Hydrocarbon vapor + H2S | Tube: Cooling Water"),
    ("Shell Material:", "SA-516 Grade 70 Carbon Steel (Normalized)"),
    ("Nominal Shell Thickness:", "10.0 mm"),
    ("Corrosion Allowance (CA):", "3.0 mm"),
    ("Minimum Required (t_min):", "7.8 mm (calculated per ASME Section VIII UG-27)")
]

for label, val in specs:
    page1.insert_text(fitz.Point(50, y), label, fontname="helv", fontsize=9.5, color=(0.3, 0.3, 0.3))
    page1.insert_text(fitz.Point(210, y), val, fontname="helv", fontsize=9.5, color=(0.05, 0.05, 0.05))
    y += 18

y += 20
page1.insert_text(fitz.Point(40, y), "2.0 EXECUTIVE SUMMARY & CRITICAL ALERT", fontname="helv", fontsize=12, color=(0.8, 0.1, 0.1))
page1.draw_line(fitz.Point(40, y + 4), fitz.Point(555, y + 4), color=(0.8, 0.8, 0.8), width=1)

y += 22
exec_summary = (
    "A thorough ultrasonic thickness measurement (UTM) and external visual inspection was conducted on "
    "Heat Exchanger E-204 during the planned CDU-1 maintenance window. Severe localized metal loss was "
    "detected in Shell Course 1 near the lower vapor inlet nozzle N3. The minimum measured wall thickness "
    "is 8.2 mm against a nominal thickness of 10.0 mm and minimum allowable thickness of 7.8 mm.\n\n"
    "Calculated remaining corrosion allowance is only 0.4 mm. Based on an annualized corrosion rate of "
    "0.257 mm/year, the estimated remaining operational life is approximately 1.55 years, requiring "
    "immediate engineering derating assessment and shortening of the re-inspection interval."
)
rect_summary = fitz.Rect(50, y, 545, y + 90)
page1.insert_textbox(rect_summary, exec_summary, fontname="helv", fontsize=9.5, color=(0.1, 0.1, 0.1))

# ==================== PAGE 2 ====================
page2 = doc.new_page(width=595, height=842)

# Page header
page2.insert_text(fitz.Point(40, 45), "MRPL CDU-1 | HEAT EXCHANGER E-204 INSPECTION REPORT", fontname="helv", fontsize=9, color=(0.5, 0.5, 0.5))
page2.draw_line(fitz.Point(40, 52), fitz.Point(555, 52), color=(0.85, 0.85, 0.85), width=0.5)

# Section 3
y = 75
page2.insert_text(fitz.Point(40, y), "3.0 ULTRASONIC THICKNESS MEASUREMENT (UTM) RESULTS", fontname="helv", fontsize=12, color=(0.1, 0.1, 0.1))
page2.draw_line(fitz.Point(40, y + 4), fitz.Point(555, y + 4), color=(0.8, 0.8, 0.8), width=1)

y += 25
# Table headers
headers = [("Component Location", 50), ("Nominal (mm)", 230), ("Min Req t_min (mm)", 310), ("Measured (mm)", 420), ("Status", 500)]
for h, x_pos in headers:
    page2.insert_text(fitz.Point(x_pos, y), h, fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))

page2.draw_line(fitz.Point(40, y + 4), fitz.Point(555, y + 4), color=(0.4, 0.4, 0.4), width=1)
y += 18

data_rows = [
    ("Shell Course 1 (Inlet Nozzle N3)", "10.0", "7.8", "8.2", "WARNING"),
    ("Shell Course 2 (Center Ring)", "10.0", "7.8", "9.1", "NORMAL"),
    ("Shell Course 3 (Outlet)", "10.0", "7.8", "9.4", "NORMAL"),
    ("Channel Head (Shell Side)", "12.0", "9.2", "11.4", "NORMAL"),
    ("Floating Head Cover", "14.0", "10.5", "13.2", "NORMAL"),
    ("Stationary Tubesheet", "25.0", "20.0", "24.6", "NORMAL"),
    ("Nozzle N1 (Crude Inlet 10-inch)", "9.27", "6.5", "8.6", "NORMAL"),
    ("Nozzle N3 (Vapor Return 8-inch)", "8.18", "5.8", "6.4", "WARNING")
]

for row in data_rows:
    comp, nom, req, meas, stat = row
    color_stat = (0.8, 0.1, 0.1) if stat == "WARNING" else (0.1, 0.6, 0.2)
    page2.insert_text(fitz.Point(50, y), comp, fontname="helv", fontsize=9, color=(0.1, 0.1, 0.1))
    page2.insert_text(fitz.Point(245, y), nom, fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
    page2.insert_text(fitz.Point(340, y), req, fontname="helv", fontsize=9, color=(0.2, 0.2, 0.2))
    page2.insert_text(fitz.Point(435, y), meas, fontname="helv", fontsize=9, color=(0.1, 0.1, 0.1))
    page2.insert_text(fitz.Point(500, y), stat, fontname="helv", fontsize=8.5, color=color_stat)
    page2.draw_line(fitz.Point(40, y + 4), fitz.Point(555, y + 4), color=(0.9, 0.9, 0.9), width=0.5)
    y += 18

y += 25
page2.insert_text(fitz.Point(40, y), "4.0 ENGINEERING CORROSION & REMAINING LIFE CALCULATIONS", fontname="helv", fontsize=12, color=(0.1, 0.1, 0.1))
page2.draw_line(fitz.Point(40, y + 4), fitz.Point(555, y + 4), color=(0.8, 0.8, 0.8), width=1)

y += 20
calc_text = (
    "Calculations performed in accordance with API 510 Section 7.1 and API 579-1 Fitness-for-Service:\n\n"
    "1. Corrosion Rate (CR):\n"
    "   CR = (t_initial - t_actual) / Time_years\n"
    "   Baseline Thickness (t_initial, Year 2018): 10.0 mm\n"
    "   Actual Minimum Thickness (t_actual, Year 2025): 8.2 mm\n"
    "   Service Duration: 7.0 years\n"
    "   CR = (10.0 - 8.2) / 7.0 = 1.80 mm / 7.0 yrs = 0.257 mm/year\n\n"
    "2. Remaining Corrosion Allowance (CA_remaining):\n"
    "   CA_remaining = t_actual - t_min\n"
    "   CA_remaining = 8.2 mm - 7.8 mm = 0.40 mm\n\n"
    "3. Remaining Life (RL):\n"
    "   RL = CA_remaining / CR\n"
    "   RL = 0.40 mm / 0.257 mm/year = 1.55 Years (~18.6 Months)\n\n"
    "Conclusion: Equipment will reach minimum allowable wall thickness (7.8 mm) by approximately May 2027 "
    "under continuous operating conditions."
)
rect_calc = fitz.Rect(50, y, 545, y + 230)
page2.insert_textbox(rect_calc, calc_text, fontname="helv", fontsize=9.5, color=(0.1, 0.1, 0.1))

# ==================== PAGE 3 ====================
page3 = doc.new_page(width=595, height=842)

# Page header
page3.insert_text(fitz.Point(40, 45), "MRPL CDU-1 | HEAT EXCHANGER E-204 INSPECTION REPORT", fontname="helv", fontsize=9, color=(0.5, 0.5, 0.5))
page3.draw_line(fitz.Point(40, 52), fitz.Point(555, 52), color=(0.85, 0.85, 0.85), width=0.5)

y = 75
page3.insert_text(fitz.Point(40, y), "5.0 RISK ASSESSMENT & FITNESS-FOR-SERVICE EVALUATION", fontname="helv", fontsize=12, color=(0.1, 0.1, 0.1))
page3.draw_line(fitz.Point(40, y + 4), fitz.Point(555, y + 4), color=(0.8, 0.8, 0.8), width=1)

y += 20
risk_text = (
    "Risk Classification: HIGH (Priority Level 1)\n\n"
    "Degradation Mechanism:\n"
    "Localized wet H2S sour water corrosion combined with erosion-corrosion turbulence from incoming crude pre-flash "
    "overhead vapors at Nozzle N3. Carbon steel SA-516 Grade 70 lacks specialized cladding or weld overlay in this section.\n\n"
    "Safety & Environmental Consequences:\n"
    "A shell breach would release toxic hydrogen sulfide (H2S) gas and hot combustible hydrocarbons at 185 deg C into "
    "the unit battery limits, posing catastrophic fire, vapor cloud explosion (VCE), and personnel toxicity risks."
)
rect_risk = fitz.Rect(50, y, 545, y + 130)
page3.insert_textbox(rect_risk, risk_text, fontname="helv", fontsize=9.5, color=(0.1, 0.1, 0.1))

y += 140
page3.insert_text(fitz.Point(40, y), "6.0 MANDATORY ENGINEERING RECOMMENDATIONS", fontname="helv", fontsize=12, color=(0.14, 0.38, 0.92))
page3.draw_line(fitz.Point(40, y + 4), fitz.Point(555, y + 4), color=(0.8, 0.8, 0.8), width=1)

y += 20
recs = [
    "1. Immediate Operating Pressure Review: Re-rate Maximum Allowable Working Pressure (MAWP) from 15.5 bar to 14.0 bar pending Level 2 assessment.",
    "2. Inspection Interval Reduction: Reduce UTM re-inspection frequency from 60 months (5 years) to 12 months (1 year). Schedule next scan for October 2026.",
    "3. Mitigation: Install an internal stainless steel (Inconel 625 or 316L) impingement plate / weld overlay beneath Nozzle N3 during the Q1 2026 turnaround.",
    "4. Online Corrosion Monitoring: Deploy electrical resistance (ER) corrosion probes on the overhead vapor line upstream of E-204.",
    "5. Engineering Review Sign-off: Certified pressure vessel engineer (API 510) formal sign-off required prior to plant re-commissioning."
]

for rec in recs:
    rect_r = fitz.Rect(50, y, 545, y + 36)
    page3.insert_textbox(rect_r, rec, fontname="helv", fontsize=9.5, color=(0.1, 0.1, 0.1))
    y += 40

# Signature section
y += 30
page3.draw_line(fitz.Point(50, y), fitz.Point(220, y), color=(0.4, 0.4, 0.4), width=1)
page3.draw_line(fitz.Point(340, y), fitz.Point(510, y), color=(0.4, 0.4, 0.4), width=1)
page3.insert_text(fitz.Point(50, y + 15), "Lead Inspection Engineer (API 510 Cert #48291)", fontname="helv", fontsize=8.5, color=(0.3, 0.3, 0.3))
page3.insert_text(fitz.Point(340, y + 15), "Chief Technical Integrity Officer, MRPL", fontname="helv", fontsize=8.5, color=(0.3, 0.3, 0.3))

doc.save(str(pdf_path))
doc.close()
print(f"Sample PDF successfully generated at {pdf_path}")
