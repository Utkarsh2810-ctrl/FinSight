from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

doc = SimpleDocTemplate(
    "/mnt/user-data/outputs/NovaTech_Q3_2024_Earnings.pdf",
    pagesize=letter,
    rightMargin=0.75*inch, leftMargin=0.75*inch,
    topMargin=0.75*inch, bottomMargin=0.75*inch
)

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle("Title", parent=styles["Normal"],
    fontSize=20, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6)
subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"],
    fontSize=12, fontName="Helvetica", alignment=TA_CENTER, spaceAfter=4, textColor=colors.grey)
h1 = ParagraphStyle("H1", parent=styles["Normal"],
    fontSize=13, fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=14)
h2 = ParagraphStyle("H2", parent=styles["Normal"],
    fontSize=11, fontName="Helvetica-Bold", spaceAfter=4, spaceBefore=10)
body = ParagraphStyle("Body", parent=styles["Normal"],
    fontSize=9.5, fontName="Helvetica", leading=14, spaceAfter=8, alignment=TA_JUSTIFY)
small = ParagraphStyle("Small", parent=styles["Normal"],
    fontSize=8.5, fontName="Helvetica", leading=12, spaceAfter=6, textColor=colors.grey)
right = ParagraphStyle("Right", parent=styles["Normal"],
    fontSize=9, fontName="Helvetica", alignment=TA_RIGHT)

HDR = colors.HexColor("#1e3a5f")
ALT = colors.HexColor("#f0f4f8")
WHT = colors.white
BLK = colors.black

def tbl_style(has_header=True):
    s = [
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHT, ALT]),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
    ]
    if has_header:
        s += [
            ("BACKGROUND", (0,0), (-1,0), HDR),
            ("TEXTCOLOR", (0,0), (-1,0), WHT),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ]
    return TableStyle(s)

story = []

# ── COVER ────────────────────────────────────────────────────────────────────
story.append(Spacer(1, 0.5*inch))
story.append(Paragraph("NOVATECH SOLUTIONS INC.", title_style))
story.append(Paragraph("Third Quarter Fiscal 2024 Earnings Report", subtitle_style))
story.append(Paragraph("For the Quarter Ended September 30, 2024", subtitle_style))
story.append(Paragraph("NASDAQ: NVTS  |  Investor Relations  |  earnings@novatech.com", subtitle_style))
story.append(Spacer(1, 0.2*inch))
story.append(HRFlowable(width="100%", thickness=1.5, color=HDR))
story.append(Spacer(1, 0.15*inch))

# Highlights box
hi_data = [
    ["Q3 2024 Financial Highlights", "", "", ""],
    ["Revenue", "$2.84B", "Net Income", "$412M"],
    ["Gross Margin", "67.3%", "EPS (Diluted)", "$3.21"],
    ["Operating Income", "$538M", "Free Cash Flow", "$701M"],
    ["YoY Revenue Growth", "+18.4%", "YoY Net Income Growth", "+24.1%"],
]
hi_tbl = Table(hi_data, colWidths=[2.2*inch, 1.5*inch, 2.2*inch, 1.5*inch])
hi_tbl.setStyle(TableStyle([
    ("SPAN", (0,0), (3,0)),
    ("BACKGROUND", (0,0), (3,0), HDR),
    ("TEXTCOLOR", (0,0), (3,0), WHT),
    ("FONTNAME", (0,0), (3,0), "Helvetica-Bold"),
    ("FONTSIZE", (0,0), (3,0), 11),
    ("ALIGN", (0,0), (3,0), "CENTER"),
    ("ROWBACKGROUNDS", (0,1), (-1,-1), [ALT, WHT]),
    ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
    ("FONTNAME", (2,1), (2,-1), "Helvetica-Bold"),
    ("FONTSIZE", (0,1), (-1,-1), 10),
    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#aaaaaa")),
    ("TOPPADDING", (0,0), (-1,-1), 5),
    ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ("LEFTPADDING", (0,0), (-1,-1), 8),
]))
story.append(hi_tbl)
story.append(Spacer(1, 0.2*inch))

# ── CEO LETTER ───────────────────────────────────────────────────────────────
story.append(Paragraph("Letter to Shareholders", h1))
story.append(HRFlowable(width="100%", thickness=0.5, color=HDR))
story.append(Spacer(1, 0.08*inch))

story.append(Paragraph(
    "Dear Shareholders,",
    body))
story.append(Paragraph(
    "NovaTech Solutions delivered another strong quarter in Q3 2024, with revenue of $2.84 billion, "
    "representing an 18.4% increase year-over-year and a 6.2% increase quarter-over-quarter from $2.67 billion "
    "in Q2 2024. This growth was driven primarily by continued momentum in our cloud infrastructure segment, "
    "which grew 34% year-over-year to $1.21 billion, as enterprise customers accelerated their digital "
    "transformation investments.", body))
story.append(Paragraph(
    "Our AI and Machine Learning Platform (AMLP) segment recorded its strongest quarter since launch, "
    "generating $487 million in revenue, up 62% year-over-year. Demand for our GenAI developer tools and "
    "enterprise inference APIs exceeded our internal forecasts, and we have increased our data center "
    "capacity investments accordingly. We expect the AMLP segment to represent over 25% of total revenue "
    "by fiscal year 2025.", body))
story.append(Paragraph(
    "Gross margin expanded to 67.3% from 64.8% in Q3 2023, reflecting favorable product mix shift toward "
    "higher-margin software and services revenue, as well as ongoing cost optimisation in our supply chain. "
    "Operating expenses as a percentage of revenue declined to 48.4% from 51.2% a year ago, demonstrating "
    "continued operating leverage as we scale.", body))
story.append(Paragraph(
    "We generated $701 million in free cash flow during the quarter, enabling us to return $280 million to "
    "shareholders through share repurchases and $95 million in dividends. Our balance sheet remains strong "
    "with $4.2 billion in cash and short-term investments and a net debt position of negative $1.8 billion "
    "(i.e., net cash positive).", body))
story.append(Paragraph(
    "Looking ahead to Q4 2024, we guide revenue in the range of $2.95 billion to $3.05 billion, implying "
    "year-over-year growth of 16% to 20%. We continue to see strong pipeline activity across all major "
    "geographies and remain confident in our full-year fiscal 2024 target of $11.1 billion to $11.3 billion "
    "in total revenue.",
    body))
story.append(Paragraph("Respectfully,", body))
story.append(Paragraph("<b>Sarah Chen</b><br/>Chief Executive Officer, NovaTech Solutions Inc.", body))
story.append(Spacer(1, 0.1*inch))

# ── FINANCIAL RESULTS ────────────────────────────────────────────────────────
story.append(Paragraph("Financial Results — Q3 2024", h1))
story.append(HRFlowable(width="100%", thickness=0.5, color=HDR))
story.append(Spacer(1, 0.08*inch))

story.append(Paragraph("Revenue by Segment", h2))
seg_data = [
    ["Business Segment", "Q3 2024 ($M)", "Q3 2023 ($M)", "YoY Change", "Q2 2024 ($M)", "QoQ Change"],
    ["Cloud Infrastructure", "1,210", "903", "+34.0%", "1,098", "+10.2%"],
    ["AI & ML Platform (AMLP)", "487", "301", "+61.8%", "402", "+21.1%"],
    ["Enterprise Software", "642", "598", "+7.4%", "631", "+1.7%"],
    ["Professional Services", "318", "297", "+7.1%", "312", "+1.9%"],
    ["Hardware & Devices", "183", "297", "−38.4%", "227", "−19.4%"],
    ["Total Revenue", "2,840", "2,396", "+18.5%", "2,670", "+6.4%"],
]
seg_tbl = Table(seg_data, colWidths=[2.1*inch, 1.0*inch, 1.0*inch, 0.85*inch, 1.0*inch, 0.85*inch])
seg_tbl.setStyle(tbl_style())
seg_tbl.setStyle(TableStyle([
    ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
    ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#dbe8f5")),
    ("ALIGN", (1,0), (-1,-1), "RIGHT"),
]))
story.append(seg_tbl)
story.append(Spacer(1, 0.08*inch))

story.append(Paragraph(
    "The Hardware & Devices segment continued its planned wind-down as NovaTech executes its strategic "
    "pivot toward software and services. Management expects this segment to represent less than 5% of "
    "total revenue by the end of fiscal 2025, down from 12.4% in fiscal 2023.", small))

story.append(Paragraph("Revenue by Geography", h2))
geo_data = [
    ["Region", "Q3 2024 ($M)", "Q3 2023 ($M)", "YoY Change", "% of Total Revenue"],
    ["North America", "1,421", "1,214", "+17.1%", "50.0%"],
    ["Europe, Middle East & Africa", "682", "551", "+23.8%", "24.0%"],
    ["Asia Pacific", "512", "439", "+16.6%", "18.0%"],
    ["Latin America & Other", "225", "192", "+17.2%", "7.9%"],
    ["Total", "2,840", "2,396", "+18.5%", "100.0%"],
]
geo_tbl = Table(geo_data, colWidths=[2.3*inch, 1.1*inch, 1.1*inch, 0.9*inch, 1.35*inch])
geo_tbl.setStyle(tbl_style())
geo_tbl.setStyle(TableStyle([
    ("FONTNAME", (0,-1), (-1,-1), "Helvetica-Bold"),
    ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#dbe8f5")),
    ("ALIGN", (1,0), (-1,-1), "RIGHT"),
]))
story.append(geo_tbl)
story.append(Spacer(1, 0.08*inch))

# ── PAGE 2 ────────────────────────────────────────────────────────────────────
story.append(PageBreak())

story.append(Paragraph("Condensed Consolidated Income Statement (Unaudited)", h1))
story.append(HRFlowable(width="100%", thickness=0.5, color=HDR))
story.append(Spacer(1, 0.08*inch))
story.append(Paragraph("(in millions USD, except per share data)", small))

inc_data = [
    ["", "Q3 2024", "Q3 2023", "9M 2024", "9M 2023"],
    ["Revenue", "$2,840", "$2,396", "$8,241", "$6,912"],
    ["Cost of Revenue", "928", "843", "2,712", "2,501"],
    ["Gross Profit", "1,912", "1,553", "5,529", "4,411"],
    ["Gross Margin %", "67.3%", "64.8%", "67.1%", "63.8%"],
    ["", "", "", "", ""],
    ["Operating Expenses:", "", "", "", ""],
    ["  Research & Development", "487", "421", "1,412", "1,198"],
    ["  Sales & Marketing", "341", "312", "991", "897"],
    ["  General & Administrative", "142", "127", "418", "372"],
    ["  Restructuring Charges", "404", "0", "404", "48"],
    ["Total Operating Expenses", "1,374", "860", "3,225", "2,515"],
    ["Operating Income", "538", "693", "2,304", "1,896"],
    ["Operating Margin %", "18.9%", "28.9%", "28.0%", "27.4%"],
    ["", "", "", "", ""],
    ["Interest Income", "48", "31", "138", "82"],
    ["Interest Expense", "(12)", "(14)", "(37)", "(43)"],
    ["Other Income / (Expense), net", "8", "(3)", "14", "(9)"],
    ["Income Before Taxes", "582", "707", "2,419", "1,926"],
    ["Income Tax Provision", "170", "375", "687", "541"],
    ["Net Income", "$412", "$332", "$1,732", "$1,385"],
    ["", "", "", "", ""],
    ["Earnings Per Share — Basic", "$3.31", "$2.64", "$13.88", "$10.98"],
    ["Earnings Per Share — Diluted", "$3.21", "$2.58", "$13.47", "$10.72"],
    ["Weighted Avg Shares — Basic (M)", "124.5", "125.8", "124.8", "126.1"],
    ["Weighted Avg Shares — Diluted (M)", "128.4", "128.7", "128.5", "129.2"],
]
inc_tbl = Table(inc_data, colWidths=[2.6*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch])
inc_tbl.setStyle(tbl_style())
inc_tbl.setStyle(TableStyle([
    ("FONTNAME", (0,3), (0,3), "Helvetica-Bold"),
    ("FONTNAME", (0,12), (0,12), "Helvetica-Bold"),
    ("FONTNAME", (0,21), (0,21), "Helvetica-Bold"),
    ("BACKGROUND", (0,3), (-1,3), colors.HexColor("#dbe8f5")),
    ("BACKGROUND", (0,12), (-1,12), colors.HexColor("#dbe8f5")),
    ("BACKGROUND", (0,21), (-1,21), colors.HexColor("#dbe8f5")),
    ("ALIGN", (1,0), (-1,-1), "RIGHT"),
    ("FONTNAME", (0,7), (0,10), "Helvetica"),
]))
story.append(inc_tbl)
story.append(Spacer(1, 0.08*inch))

story.append(Paragraph(
    "Note: Q3 2024 operating income includes a one-time restructuring charge of $404 million related to "
    "the wind-down of the Hardware & Devices segment and associated workforce reduction of approximately "
    "1,200 positions. Excluding this charge, adjusted operating income was $942 million and adjusted "
    "operating margin was 33.2%.", small))

story.append(Paragraph("Condensed Consolidated Balance Sheet (Unaudited)", h1))
story.append(HRFlowable(width="100%", thickness=0.5, color=HDR))
story.append(Spacer(1, 0.08*inch))
story.append(Paragraph("(in millions USD, as of September 30, 2024 and December 31, 2023)", small))

bal_data = [
    ["ASSETS", "Sep 30, 2024", "Dec 31, 2023"],
    ["Cash and Cash Equivalents", "$1,842", "$1,421"],
    ["Short-Term Investments", "2,358", "1,987"],
    ["Accounts Receivable, net", "1,104", "923"],
    ["Inventories", "287", "341"],
    ["Prepaid Expenses & Other", "312", "278"],
    ["Total Current Assets", "5,903", "4,950"],
    ["Property, Plant & Equipment, net", "1,842", "1,654"],
    ["Operating Lease Right-of-Use Assets", "412", "387"],
    ["Intangible Assets, net", "892", "978"],
    ["Goodwill", "2,341", "2,341"],
    ["Other Long-Term Assets", "287", "241"],
    ["Total Assets", "$11,677", "$10,551"],
    ["", "", ""],
    ["LIABILITIES AND STOCKHOLDERS' EQUITY", "", ""],
    ["Accounts Payable", "$487", "$412"],
    ["Accrued Compensation", "342", "287"],
    ["Deferred Revenue (Current)", "612", "541"],
    ["Other Current Liabilities", "287", "231"],
    ["Total Current Liabilities", "1,728", "1,471"],
    ["Long-Term Debt", "398", "412"],
    ["Deferred Revenue (Long-Term)", "287", "241"],
    ["Other Long-Term Liabilities", "198", "187"],
    ["Total Liabilities", "2,611", "2,311"],
    ["Total Stockholders' Equity", "9,066", "8,240"],
    ["Total Liabilities & Equity", "$11,677", "$10,551"],
]
bal_tbl = Table(bal_data, colWidths=[3.5*inch, 1.5*inch, 1.5*inch])
bal_tbl.setStyle(tbl_style())
bal_tbl.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,0), HDR),
    ("TEXTCOLOR", (0,0), (-1,0), WHT),
    ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ("FONTNAME", (0,6), (0,6), "Helvetica-Bold"),
    ("FONTNAME", (0,12), (0,12), "Helvetica-Bold"),
    ("FONTNAME", (0,14), (0,14), "Helvetica-Bold"),
    ("FONTNAME", (0,19), (0,19), "Helvetica-Bold"),
    ("FONTNAME", (0,24), (0,24), "Helvetica-Bold"),
    ("FONTNAME", (0,25), (0,25), "Helvetica-Bold"),
    ("BACKGROUND", (0,6), (-1,6), colors.HexColor("#dbe8f5")),
    ("BACKGROUND", (0,12), (-1,12), colors.HexColor("#dbe8f5")),
    ("BACKGROUND", (0,19), (-1,19), colors.HexColor("#dbe8f5")),
    ("BACKGROUND", (0,25), (-1,25), colors.HexColor("#dbe8f5")),
    ("ALIGN", (1,0), (-1,-1), "RIGHT"),
]))
story.append(bal_tbl)

# ── PAGE 3 ────────────────────────────────────────────────────────────────────
story.append(PageBreak())

story.append(Paragraph("Management Discussion & Analysis", h1))
story.append(HRFlowable(width="100%", thickness=0.5, color=HDR))
story.append(Spacer(1, 0.08*inch))

story.append(Paragraph("Revenue Discussion", h2))
story.append(Paragraph(
    "Total revenue for Q3 2024 was $2.84 billion, an increase of $444 million or 18.5% compared to "
    "$2.396 billion in Q3 2023. On a constant currency basis, revenue grew approximately 20.1%, as "
    "foreign exchange headwinds, primarily from a stronger US dollar against the Euro and Japanese Yen, "
    "reduced reported revenue by approximately $38 million during the quarter.", body))
story.append(Paragraph(
    "Cloud Infrastructure revenue grew $307 million or 34.0% year-over-year to $1.21 billion, driven by "
    "a 41% increase in compute revenue and a 28% increase in storage revenue. Average revenue per enterprise "
    "customer increased 22% year-over-year to $847,000 annually, reflecting upsell success and expansion "
    "within existing accounts. The number of customers with annual contract value exceeding $1 million "
    "increased to 412 from 287 a year ago.", body))
story.append(Paragraph(
    "AI & ML Platform revenue of $487 million grew 61.8% year-over-year and 21.1% quarter-over-quarter. "
    "Growth was driven by strong adoption of NovaTech's GenAI APIs, which processed 2.4 trillion tokens "
    "during the quarter, up from 800 billion tokens in Q3 2023. The number of active AI Platform developers "
    "reached 187,000, up 94% year-over-year.", body))

story.append(Paragraph("Gross Margin Discussion", h2))
story.append(Paragraph(
    "Gross margin expanded 250 basis points year-over-year to 67.3%. The primary drivers of margin "
    "expansion were: (1) revenue mix shift toward higher-margin cloud and AI software (collectively 60% "
    "of revenue versus 50% a year ago), (2) improved infrastructure utilisation rates rising to 78% from "
    "71% in Q3 2023, and (3) renegotiated data center colocation agreements reducing per-unit hosting costs "
    "by approximately 8%. These gains were partially offset by increased GPU procurement costs associated "
    "with expanding AI inference capacity.", body))

story.append(Paragraph("Operating Expenses Discussion", h2))
story.append(Paragraph(
    "Research and development expense increased $66 million or 15.7% to $487 million, representing 17.1% "
    "of revenue versus 17.6% in Q3 2023. The increase reflects continued investment in AI capabilities, "
    "security infrastructure, and next-generation cloud services. Headcount in R&D increased to 8,412 "
    "from 7,634 a year ago.", body))
story.append(Paragraph(
    "Sales and marketing expense increased $29 million or 9.3% to $341 million, representing 12.0% of "
    "revenue versus 13.0% in Q3 2023, reflecting continued leverage as our enterprise sales motion matures. "
    "General and administrative expense was $142 million or 5.0% of revenue, down from 5.3% a year ago.", body))
story.append(Paragraph(
    "During Q3 2024, the company recorded a one-time restructuring charge of $404 million related to the "
    "strategic wind-down of the Hardware & Devices segment. This charge includes $241 million in asset "
    "write-downs, $118 million in employee severance and termination benefits for approximately 1,200 "
    "affected employees, and $45 million in contract termination costs.", body))

story.append(Paragraph("Liquidity and Capital Resources", h2))

cash_data = [
    ["Cash Flow Summary ($M)", "Q3 2024", "Q3 2023", "9M 2024", "9M 2023"],
    ["Net Income", "$412", "$332", "$1,732", "$1,385"],
    ["Depreciation & Amortisation", "187", "162", "548", "471"],
    ["Stock-Based Compensation", "124", "108", "368", "312"],
    ["Changes in Working Capital", "(47)", "(38)", "(142)", "(87)"],
    ["Other Operating Items", "25", "18", "72", "51"],
    ["Cash from Operations", "701", "582", "2,578", "2,132"],
    ["Capital Expenditures", "(187)", "(148)", "(541)", "(432)"],
    ["Free Cash Flow", "$701", "$582", "$2,578", "$2,132"],
    ["Acquisitions, net of cash", "(0)", "(42)", "(0)", "(198)"],
    ["Share Repurchases", "(280)", "(241)", "(842)", "(712)"],
    ["Dividends Paid", "(95)", "(82)", "(283)", "(241)"],
    ["Net Change in Cash", "$139", "$112", "$412", "$387"],
]
cash_tbl = Table(cash_data, colWidths=[2.6*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch])
cash_tbl.setStyle(tbl_style())
cash_tbl.setStyle(TableStyle([
    ("FONTNAME", (0,6), (0,6), "Helvetica-Bold"),
    ("FONTNAME", (0,8), (0,8), "Helvetica-Bold"),
    ("FONTNAME", (0,-1), (0,-1), "Helvetica-Bold"),
    ("BACKGROUND", (0,6), (-1,6), colors.HexColor("#dbe8f5")),
    ("BACKGROUND", (0,8), (-1,8), colors.HexColor("#dbe8f5")),
    ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#dbe8f5")),
    ("ALIGN", (1,0), (-1,-1), "RIGHT"),
]))
story.append(cash_tbl)
story.append(Spacer(1, 0.08*inch))

story.append(Paragraph(
    "As of September 30, 2024, the company held $4.2 billion in cash and short-term investments and "
    "$398 million in long-term debt, resulting in a net cash position of $3.8 billion. The company has "
    "$1.5 billion remaining under its current share repurchase authorisation and expects to complete this "
    "programme by the end of Q2 2025.", body))

# ── PAGE 4 ────────────────────────────────────────────────────────────────────
story.append(PageBreak())

story.append(Paragraph("Forward Guidance and Outlook", h1))
story.append(HRFlowable(width="100%", thickness=0.5, color=HDR))
story.append(Spacer(1, 0.08*inch))

story.append(Paragraph("Q4 2024 Guidance", h2))
q4_data = [
    ["Metric", "Q4 2024 Guidance", "Q4 2023 Actual", "Implied YoY Growth"],
    ["Total Revenue", "$2,950M – $3,050M", "$2,541M", "+16.1% – +20.0%"],
    ["Gross Margin (GAAP)", "67.0% – 68.0%", "65.2%", "+180 to +280 bps"],
    ["Operating Income (GAAP)", "$870M – $920M", "$721M", "+20.7% – +27.6%"],
    ["EPS Diluted (GAAP)", "$3.45 – $3.65", "$2.87", "+20.2% – +27.2%"],
    ["Capital Expenditures", "~$210M", "$162M", "+29.6%"],
]
q4_tbl = Table(q4_data, colWidths=[2.1*inch, 1.8*inch, 1.4*inch, 1.6*inch])
q4_tbl.setStyle(tbl_style())
story.append(q4_tbl)
story.append(Spacer(1, 0.08*inch))

story.append(Paragraph("Full Year 2024 Guidance (Updated)", h2))
fy_data = [
    ["Metric", "FY 2024 Updated Guidance", "FY 2024 Prior Guidance", "FY 2023 Actual"],
    ["Total Revenue", "$11,100M – $11,300M", "$10,800M – $11,200M", "$9,487M"],
    ["Gross Margin (GAAP)", "67.0% – 67.5%", "65.5% – 66.5%", "64.1%"],
    ["Operating Income (GAAP)", "$2,800M – $2,900M", "$2,600M – $2,800M", "$2,312M"],
    ["EPS Diluted (GAAP)", "$13.10 – $13.50", "$12.50 – $13.20", "$10.87"],
    ["Free Cash Flow", "~$3,200M", "~$2,900M", "$2,541M"],
]
fy_tbl = Table(fy_data, colWidths=[2.1*inch, 1.8*inch, 1.8*inch, 1.2*inch])
fy_tbl.setStyle(tbl_style())
story.append(fy_tbl)
story.append(Spacer(1, 0.08*inch))

story.append(Paragraph(
    "Management has raised full-year 2024 revenue guidance by $200 million at the midpoint, reflecting "
    "stronger-than-anticipated demand in the Cloud Infrastructure and AI & ML Platform segments, partially "
    "offset by earlier-than-expected wind-down of the Hardware & Devices segment. The guidance range assumes "
    "foreign exchange rates remain roughly consistent with Q3 2024 average rates.", body))

story.append(Paragraph("Strategic Priorities for 2025", h2))
story.append(Paragraph(
    "<b>1. AI Platform Expansion:</b> NovaTech plans to launch NovaMind 2.0, its next-generation enterprise "
    "AI development platform, in Q1 2025. The platform will include support for multi-modal models, "
    "fine-tuning capabilities, and enterprise-grade compliance and data residency controls. Management "
    "targets $2.5 billion in AMLP revenue for fiscal 2025.", body))
story.append(Paragraph(
    "<b>2. International Expansion:</b> The company plans to open three new data center regions in fiscal "
    "2025 — Frankfurt (Germany), Mumbai (India), and São Paulo (Brazil) — expanding its infrastructure "
    "footprint to 24 regions globally. These investments are expected to add approximately $180 million "
    "in capital expenditures in fiscal 2025.", body))
story.append(Paragraph(
    "<b>3. Enterprise Security:</b> Following the acquisition of SecureLayer Inc. in Q1 2024 for $198 "
    "million, NovaTech will integrate SecureLayer's zero-trust network access technology into its cloud "
    "platform in H1 2025. The combined offering is expected to target the $42 billion enterprise security "
    "market.", body))
story.append(Paragraph(
    "<b>4. Segment Restructuring:</b> The wind-down of the Hardware & Devices segment is expected to be "
    "substantially complete by Q2 2025. The approximately 1,200 employees affected by the restructuring "
    "will receive severance packages averaging 16 weeks of pay, plus extended health benefits and outplacement "
    "services.", body))

story.append(Paragraph("Key Operating Metrics", h2))
kpi_data = [
    ["Metric", "Q3 2024", "Q3 2023", "YoY Change"],
    ["Total Customers", "24,812", "19,341", "+28.3%"],
    ["Enterprise Customers (>$100K ARR)", "3,412", "2,287", "+49.2%"],
    ["Net Revenue Retention Rate", "118%", "112%", "+6 pts"],
    ["Annual Recurring Revenue (ARR)", "$9.8B", "$7.4B", "+32.4%"],
    ["Remaining Performance Obligations", "$14.2B", "$10.1B", "+40.6%"],
    ["Headcount (Total)", "21,487", "19,842", "+8.3%"],
    ["R&D Headcount", "8,412", "7,634", "+10.2%"],
    ["Data Processed (Exabytes)", "4.8", "3.1", "+54.8%"],
    ["AI Tokens Processed (Trillions)", "2.4", "0.8", "+200.0%"],
    ["Platform Uptime SLA Achievement", "99.97%", "99.94%", "+3 bps"],
]
kpi_tbl = Table(kpi_data, colWidths=[2.8*inch, 1.3*inch, 1.3*inch, 1.2*inch])
kpi_tbl.setStyle(tbl_style())
story.append(kpi_tbl)
story.append(Spacer(1, 0.1*inch))

# Footer disclaimer
story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
story.append(Spacer(1, 0.05*inch))
story.append(Paragraph(
    "This document contains forward-looking statements within the meaning of the Private Securities "
    "Litigation Reform Act of 1995. Forward-looking statements involve risks and uncertainties that could "
    "cause actual results to differ materially from those projected. NovaTech Solutions Inc. undertakes no "
    "obligation to update forward-looking statements. All figures are unaudited. NovaTech Solutions Inc. "
    "is a fictional company created for demonstration purposes only.", small))

doc.build(story)
print("PDF generated successfully.")