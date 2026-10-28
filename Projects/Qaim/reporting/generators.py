"""Reporting module — export and report generation.

Stage 1: CSV/XLSX export (implemented in API routes)
Stage 5: Full valuation report generation (scaffolded here)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ReportGenerator(ABC):
    """Base class for report generators."""
    
    @abstractmethod
    def generate(
        self,
        case_data: Dict[str, Any],
        template_id: Optional[str] = None,
    ) -> bytes:
        """Generate a report and return the file bytes."""
        pass


class CompSummaryPDFGenerator(ReportGenerator):
    """Generate a simple 1-2 page comparable summary PDF.
    
    Stage 1: basic implementation
    """
    
    def generate(self, case_data: Dict[str, Any], template_id: Optional[str] = None) -> bytes:
        """Generate a simple PDF summary of comparables."""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import mm
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib import colors
            import io
            
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            # Title
            elements.append(Paragraph(
                f"Comparable Summary — {case_data.get('title', 'Untitled Case')}",
                styles['Title']
            ))
            elements.append(Spacer(1, 10 * mm))
            
            # Case info
            elements.append(Paragraph(
                f"City: {case_data.get('city', 'N/A')} | "
                f"Comparables: {len(case_data.get('comparables', []))}",
                styles['Normal']
            ))
            elements.append(Spacer(1, 5 * mm))
            
            # Comps table
            comps = case_data.get("comparables", [])
            if comps:
                headers = ["#", "Title", "City", "District", "Type", "Price (SAR)", "Area (sqm)", "SAR/sqm", "Evidence"]
                table_data = [headers]
                for i, c in enumerate(comps, 1):
                    table_data.append([
                        str(i),
                        str(c.get("property_title", "Unknown"))[:30],
                        str(c.get("city", "")),
                        str(c.get("district", "")),
                        str(c.get("property_subtype", "")),
                        f"{c.get('asking_price', '') or c.get('transacted_price', '')}",
                        str(c.get("land_area", "")),
                        str(c.get("price_per_sqm", "")),
                        str(c.get("evidence_type", "")),
                    ])
                
                table = Table(table_data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2E4057')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ]))
                elements.append(table)
            
            doc.build(elements)
            return buffer.getvalue()
            
        except ImportError:
            return b"reportlab not installed — PDF generation unavailable"


class FullValuationReportGenerator(ReportGenerator):
    """Stage 5: Full valuation report in Word/PDF."""
    
    def generate(self, case_data: Dict[str, Any], template_id: Optional[str] = None) -> bytes:
        # TODO: Stage 5 — implement template-driven report with narrative
        raise NotImplementedError("Stage 5")
