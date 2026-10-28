"""
Simple 1-2 page Comparable Summary PDF.
Uses reportlab for generation.
"""

import io
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_pdf_summary(case: Any, comps_with_fields: list[tuple]) -> io.BytesIO:
    """Generate a simple comparable summary PDF."""
    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()

    elements = []

    # Title
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"], fontSize=16, spaceAfter=12
    )
    elements.append(Paragraph(f"Comparable Summary — {case.title}", title_style))
    elements.append(Paragraph(
        f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} | "
        f"Comparables: {len(comps_with_fields)}",
        styles["Normal"],
    ))
    elements.append(Spacer(1, 10*mm))

    if not comps_with_fields:
        elements.append(Paragraph("No comparables extracted yet.", styles["Normal"]))
        doc.build(elements)
        output.seek(0)
        return output

    # Summary table
    headers = [
        "Source", "City", "District", "Type", "Evidence",
        "Price (SAR)", "Area (sqm)", "SAR/sqm", "Date", "Status"
    ]
    data = [headers]

    for comp, fields, source in comps_with_fields:
        price = comp.asking_price or comp.transacted_price
        data.append([
            (source.url or source.file_name or "")[:30] if source else "",
            comp.city or "",
            comp.district or "",
            (comp.property_type or "")[:12],
            (comp.evidence_type or "")[:12],
            f"{price:,.0f}" if price else "",
            f"{comp.primary_area_sqm:,.0f}" if comp.primary_area_sqm else "",
            f"{comp.price_per_sqm:,.0f}" if comp.price_per_sqm else "",
            comp.listing_date or comp.transaction_date or "",
            comp.status,
        ])

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (5, 1), (7, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(table)

    # Disclaimer
    elements.append(Spacer(1, 10*mm))
    disclaimer = ParagraphStyle("Disclaimer", parent=styles["Normal"], fontSize=7, textColor=colors.grey)
    elements.append(Paragraph(
        "This summary is for internal use only. All values require independent verification. "
        "Asking prices do not represent achieved transactions unless explicitly stated.",
        disclaimer,
    ))

    doc.build(elements)
    output.seek(0)
    return output
