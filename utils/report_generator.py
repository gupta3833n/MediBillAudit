"""
Generates a professional PDF audit report using ReportLab.
Falls back to a styled HTML report if ReportLab is not available.
"""

import io
from datetime import datetime
from typing import Optional


# ─── Colour palette ───────────────────────────────────────────────────────────
RED_HEX = "#C62828"
ORANGE_HEX = "#E65100"
YELLOW_HEX = "#F57F17"
GREEN_HEX = "#2E7D32"
BLUE_HEX = "#1565C0"
GREY_HEX = "#424242"
LIGHT_RED = "#FFEBEE"
LIGHT_YELLOW = "#FFF8E1"
LIGHT_GREEN = "#E8F5E9"
LIGHT_BLUE = "#E3F2FD"
LIGHT_GREY = "#F5F5F5"
HEADER_BG = "#0D47A1"


def _flag_color(flag: str) -> str:
    mapping = {
        "OVERCHARGED": RED_HEX,
        "MAJOR OVERCHARGE": RED_HEX,
        "SUSPICIOUS": ORANGE_HEX,
        "SLIGHTLY HIGH": YELLOW_HEX,
        "FAIR": GREEN_HEX,
        "BELOW BENCHMARK": BLUE_HEX,
        "UNKNOWN": GREY_HEX,
    }
    return mapping.get(flag.upper(), GREY_HEX)


def _score_color(score: int) -> str:
    if score >= 75:
        return GREEN_HEX
    if score >= 50:
        return YELLOW_HEX
    return RED_HEX


def generate_pdf_report(
    patient_info: dict,
    analysis_results: list[dict],
    summary: dict,
) -> bytes:
    """
    Generate a PDF audit report.
    Returns raw PDF bytes, or falls back to HTML bytes encoded as UTF-8 if ReportLab unavailable.
    """
    try:
        return _generate_reportlab_pdf(patient_info, analysis_results, summary)
    except ImportError:
        html = _generate_html_report(patient_info, analysis_results, summary)
        return html.encode("utf-8")


def _generate_reportlab_pdf(
    patient_info: dict,
    analysis_results: list[dict],
    summary: dict,
) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        fontSize=20,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor(HEADER_BG),
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontSize=11,
        textColor=colors.HexColor(GREY_HEX),
        alignment=TA_CENTER,
        spaceAfter=2,
    )
    section_style = ParagraphStyle(
        "Section",
        fontSize=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor(HEADER_BG),
        spaceBefore=12,
        spaceAfter=6,
    )
    normal = ParagraphStyle(
        "Normal2",
        fontSize=9,
        textColor=colors.HexColor(GREY_HEX),
        spaceAfter=2,
    )
    bold_label = ParagraphStyle(
        "Bold",
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=colors.black,
    )

    story.append(Paragraph("MediBill Audit", title_style))
    story.append(Paragraph("AI-Powered Hospital Bill Audit Report", subtitle_style))
    story.append(
        Paragraph(
            f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor(HEADER_BG)))
    story.append(Spacer(1, 0.3 * cm))

    # ── Patient Info ──────────────────────────────────────────────────────────
    story.append(Paragraph("Patient & Bill Information", section_style))
    info_data = [
        ["Patient Name", patient_info.get("name", "N/A"), "Bill Number", patient_info.get("bill_number", "N/A")],
        ["Age / Gender", f"{patient_info.get('age', 'N/A')} yrs / {patient_info.get('gender', 'N/A')}", "Bill Date", patient_info.get("bill_date", "N/A")],
        ["Hospital", patient_info.get("hospital", "N/A"), "Admission Date", patient_info.get("admission_date", "N/A")],
        ["Diagnosis", patient_info.get("diagnosis", "N/A"), "Discharge Date", patient_info.get("discharge_date", "N/A")],
        ["Attending Doctor", patient_info.get("attending_doctor", "N/A"), "Duration", f"{patient_info.get('duration_days', 'N/A')} days"],
    ]
    info_table = Table(info_data, colWidths=[3.5 * cm, 7 * cm, 3.5 * cm, 5.5 * cm])
    info_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDBDBD")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E0E0E0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(info_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── Summary Box ───────────────────────────────────────────────────────────
    story.append(Paragraph("Audit Summary", section_style))
    score = summary.get("health_score", 0)
    score_col = colors.HexColor(_score_color(score))
    summary_data = [
        [
            f"₹{summary.get('total_billed', 0):,.0f}",
            f"₹{summary.get('total_fair', 0):,.0f}",
            f"₹{summary.get('potential_savings', 0):,.0f}",
            f"{score}/100",
        ],
        ["Total Billed", "Fair Estimate", "Potential Savings", "Bill Health Score"],
        [
            f"{summary.get('items_overcharged', 0)} items",
            f"{summary.get('items_suspicious', 0)} items",
            f"{summary.get('items_fair', 0)} items",
            f"{summary.get('items_unknown', 0)} items",
        ],
        ["Overcharged", "Suspicious", "Fair / OK", "Unmatched"],
    ]
    summary_table = Table(summary_data, colWidths=[4.75 * cm] * 4)
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, 0), 14),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, 1), 8),
                ("FONTSIZE", (0, 2), (-1, 2), 10),
                ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                ("FONTSIZE", (0, 3), (-1, 3), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TEXTCOLOR", (0, 0), (0, 0), colors.HexColor(RED_HEX)),
                ("TEXTCOLOR", (1, 0), (1, 0), colors.HexColor(GREEN_HEX)),
                ("TEXTCOLOR", (2, 0), (2, 0), colors.HexColor(ORANGE_HEX)),
                ("TEXTCOLOR", (3, 0), (3, 0), score_col),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(LIGHT_BLUE)),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor(HEADER_BG)),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#BBDEFB")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.3 * cm))

    # ── Bill Items Table ───────────────────────────────────────────────────────
    story.append(Paragraph("Detailed Bill Analysis", section_style))

    table_header = [
        "Item Description",
        "Category",
        "Qty",
        "Billed Rate (₹)",
        "Benchmark (₹)",
        "Variance",
        "Billed Amt (₹)",
        "Fair Amt (₹)",
        "Status",
    ]
    table_data = [table_header]

    for r in analysis_results:
        variance_str = (
            f"{r['variance_pct']:+.0f}%"
            if r.get("variance_pct") is not None
            else "—"
        )
        bench_str = (
            f"{r['benchmark_rate']:,.0f}"
            if r.get("benchmark_rate") is not None
            else "—"
        )
        row = [
            r.get("name", ""),
            r.get("category", ""),
            f"{r.get('quantity', 1):.0f}",
            f"{r.get('unit_rate', r.get('amount', 0)):,.0f}",
            bench_str,
            variance_str,
            f"{r.get('amount', 0):,.0f}",
            f"{r.get('fair_amount', r.get('amount', 0)):,.0f}",
            r.get("flag", ""),
        ]
        table_data.append(row)

    col_widths = [4.5 * cm, 2.5 * cm, 0.8 * cm, 2 * cm, 2 * cm, 1.5 * cm, 2 * cm, 2 * cm, 2.2 * cm]
    items_table = Table(table_data, colWidths=col_widths, repeatRows=1)

    ts = [
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(HEADER_BG)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDBDBD")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E0E0E0")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFAFA")]),
    ]

    # Colour-code rows by flag
    for i, r in enumerate(analysis_results, start=1):
        flag = r.get("flag", "").upper()
        if "OVERCHARGE" in flag:
            ts.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FFEBEE")))
            ts.append(("TEXTCOLOR", (8, i), (8, i), colors.HexColor(RED_HEX)))
        elif flag == "SUSPICIOUS":
            ts.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FFF3E0")))
            ts.append(("TEXTCOLOR", (8, i), (8, i), colors.HexColor(ORANGE_HEX)))
        elif flag in ("SLIGHTLY HIGH",):
            ts.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor(LIGHT_YELLOW)))
            ts.append(("TEXTCOLOR", (8, i), (8, i), colors.HexColor(YELLOW_HEX)))
        elif flag == "FAIR":
            ts.append(("TEXTCOLOR", (8, i), (8, i), colors.HexColor(GREEN_HEX)))

    items_table.setStyle(TableStyle(ts))
    story.append(items_table)
    story.append(Spacer(1, 0.4 * cm))

    # ── Recommendations ────────────────────────────────────────────────────────
    story.append(Paragraph("Recommendations", section_style))
    recommendations = _build_recommendations(analysis_results, summary)
    for i, rec in enumerate(recommendations, 1):
        story.append(
            Paragraph(
                f"{i}. {rec}",
                ParagraphStyle(
                    "Rec",
                    fontSize=9,
                    spaceAfter=5,
                    leftIndent=10,
                    textColor=colors.HexColor(GREY_HEX),
                ),
            )
        )

    story.append(Spacer(1, 0.4 * cm))

    # ── Disclaimer ─────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#BDBDBD")))
    story.append(
        Paragraph(
            "DISCLAIMER: This report is generated by an AI system for informational purposes only. "
            "Benchmark rates are indicative averages for Tier-1 Indian cities and may vary by hospital "
            "category, location, and specific circumstances. This report does not constitute legal advice. "
            "Consult a qualified healthcare advocate or legal professional for disputes.",
            ParagraphStyle(
                "Disclaimer",
                fontSize=7.5,
                textColor=colors.HexColor("#9E9E9E"),
                alignment=TA_CENTER,
                spaceBefore=8,
            ),
        )
    )
    story.append(
        Paragraph(
            "Report generated by MediBill Audit | AICA Capstone Project",
            ParagraphStyle(
                "Footer",
                fontSize=7.5,
                textColor=colors.HexColor("#BDBDBD"),
                alignment=TA_CENTER,
                spaceBefore=4,
            ),
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _build_recommendations(results: list[dict], summary: dict) -> list[str]:
    recs = []
    savings = summary.get("potential_savings", 0)
    if savings > 0:
        recs.append(
            f"Request itemised bill clarification from the hospital. You may be entitled to "
            f"a refund of approximately ₹{savings:,.0f} based on our benchmark analysis."
        )

    overcharged = [r for r in results if "OVERCHARGE" in r.get("flag", "").upper()]
    if overcharged:
        top = sorted(overcharged, key=lambda x: x.get("overcharge_amount", 0), reverse=True)[:3]
        names = ", ".join(r["name"] for r in top)
        recs.append(f"Highest overcharges detected in: {names}. Ask the hospital to justify these rates.")

    suspicious = [r for r in results if r.get("flag", "").upper() == "SUSPICIOUS"]
    if suspicious:
        names = ", ".join(r["name"] for r in suspicious)
        recs.append(
            f"Suspicious/duplicate items found: {names}. "
            "These charges may be incorrectly billed or already included in room/procedure charges."
        )

    recs.append(
        "You have the right to request an itemised bill from any hospital in India under the Consumer Protection Act."
    )
    recs.append(
        "If overcharging is confirmed, you may file a complaint with the State Medical Council or "
        "the National Consumer Disputes Redressal Commission (NCDRC)."
    )
    if summary.get("health_score", 100) < 60:
        recs.append(
            "Consider seeking a second opinion or consulting a medical billing advocate before making payment."
        )
    return recs


def _generate_html_report(
    patient_info: dict,
    analysis_results: list[dict],
    summary: dict,
) -> str:
    """Fallback: generate a styled HTML report."""
    score = summary.get("health_score", 0)
    score_color = _score_color(score)
    date_str = datetime.now().strftime("%d %B %Y, %I:%M %p")

    rows_html = ""
    for r in analysis_results:
        flag = r.get("flag", "").upper()
        if "OVERCHARGE" in flag:
            row_style = f"background:{LIGHT_RED}"
            flag_style = f"color:{RED_HEX};font-weight:bold"
        elif flag == "SUSPICIOUS":
            row_style = "background:#FFF3E0"
            flag_style = f"color:{ORANGE_HEX};font-weight:bold"
        elif flag == "SLIGHTLY HIGH":
            row_style = f"background:{LIGHT_YELLOW}"
            flag_style = f"color:{YELLOW_HEX};font-weight:bold"
        elif flag == "FAIR":
            row_style = f"background:{LIGHT_GREEN}"
            flag_style = f"color:{GREEN_HEX};font-weight:bold"
        else:
            row_style = ""
            flag_style = f"color:{GREY_HEX}"

        bench_str = f"₹{r['benchmark_rate']:,.0f}" if r.get("benchmark_rate") else "—"
        var_str = (
            f"{r['variance_pct']:+.0f}%" if r.get("variance_pct") is not None else "—"
        )
        rows_html += f"""
        <tr style="{row_style}">
            <td>{r.get('name','')}</td>
            <td>{r.get('category','')}</td>
            <td style="text-align:center">{r.get('quantity',1):.0f}</td>
            <td style="text-align:right">₹{r.get('unit_rate', r.get('amount',0)):,.0f}</td>
            <td style="text-align:right">{bench_str}</td>
            <td style="text-align:center">{var_str}</td>
            <td style="text-align:right">₹{r.get('amount',0):,.0f}</td>
            <td style="text-align:right">₹{r.get('fair_amount', r.get('amount',0)):,.0f}</td>
            <td style="text-align:center;{flag_style}">{r.get('flag','')}</td>
        </tr>"""

    recs = _build_recommendations(analysis_results, summary)
    recs_html = "".join(f"<li>{rec}</li>" for rec in recs)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>MediBill Audit Report</title>
<style>
  body {{ font-family: Arial, sans-serif; margin: 30px; color: #333; }}
  h1 {{ color: {HEADER_BG}; }} h2 {{ color: {HEADER_BG}; border-bottom: 2px solid {HEADER_BG}; padding-bottom:4px; }}
  .header {{ text-align:center; background:{HEADER_BG}; color:white; padding:20px; border-radius:8px; }}
  .summary-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:16px 0; }}
  .metric {{ background:#EEF2FF; border-radius:8px; padding:14px; text-align:center; }}
  .metric .value {{ font-size:22px; font-weight:bold; }}
  table {{ width:100%; border-collapse:collapse; margin:12px 0; font-size:13px; }}
  th {{ background:{HEADER_BG}; color:white; padding:8px; text-align:left; }}
  td {{ padding:7px 8px; border-bottom:1px solid #E0E0E0; }}
  .disclaimer {{ font-size:11px; color:#9E9E9E; margin-top:20px; border-top:1px solid #E0E0E0; padding-top:10px; }}
</style>
</head>
<body>
<div class="header"><h1>MediBill Audit</h1><p>AI-Powered Hospital Bill Audit Report</p><small>Generated: {date_str}</small></div>

<h2>Patient Information</h2>
<table><tr><th>Field</th><th>Details</th><th>Field</th><th>Details</th></tr>
<tr><td><b>Patient Name</b></td><td>{patient_info.get('name','N/A')}</td><td><b>Bill Number</b></td><td>{patient_info.get('bill_number','N/A')}</td></tr>
<tr><td><b>Hospital</b></td><td>{patient_info.get('hospital','N/A')}</td><td><b>Diagnosis</b></td><td>{patient_info.get('diagnosis','N/A')}</td></tr>
<tr><td><b>Admission</b></td><td>{patient_info.get('admission_date','N/A')}</td><td><b>Discharge</b></td><td>{patient_info.get('discharge_date','N/A')}</td></tr>
</table>

<h2>Audit Summary</h2>
<div class="summary-grid">
<div class="metric"><div class="value" style="color:{RED_HEX}">₹{summary.get('total_billed',0):,.0f}</div><div>Total Billed</div></div>
<div class="metric"><div class="value" style="color:{GREEN_HEX}">₹{summary.get('total_fair',0):,.0f}</div><div>Fair Estimate</div></div>
<div class="metric"><div class="value" style="color:{ORANGE_HEX}">₹{summary.get('potential_savings',0):,.0f}</div><div>Potential Savings</div></div>
<div class="metric"><div class="value" style="color:{score_color}">{score}/100</div><div>Health Score</div></div>
</div>

<h2>Detailed Bill Analysis</h2>
<table>
<tr><th>Item</th><th>Category</th><th>Qty</th><th>Billed Rate</th><th>Benchmark</th><th>Variance</th><th>Billed Amt</th><th>Fair Amt</th><th>Status</th></tr>
{rows_html}
</table>

<h2>Recommendations</h2><ol>{recs_html}</ol>

<div class="disclaimer">DISCLAIMER: This report is for informational purposes only. Benchmark rates are indicative averages for Tier-1 Indian cities.
Consult a qualified healthcare advocate or legal professional for disputes. Report generated by MediBill Audit | AICA Capstone Project.</div>
</body></html>"""
