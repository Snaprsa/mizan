"""
Report Generator — Stage 5 scaffold.

Will generate full valuation reports from:
- Subject property profile
- Selected comparables with adjustments
- Valuation run results
- Approved assumptions and judgments
- Template structure

RULES:
- Narrative generated ONLY from approved data
- Every statement must be traceable to a fact/assumption/judgment
- No hallucinated content
- Support TAQEEM/RICS standard structures
"""

from typing import Optional


class ReportGenerator:
    """Generate valuation reports from templates and approved data."""

    def __init__(self):
        # TODO: Load templates from reporting/templates/
        pass

    async def generate(
        self,
        case_id: str,
        template_id: Optional[str] = None,
        format: str = "docx",
    ) -> bytes:
        """
        Generate a full valuation report.

        Args:
            case_id: UUID of the case
            template_id: UUID of the template to use (or default)
            format: Output format (docx, pdf)

        Returns:
            Report file bytes
        """
        raise NotImplementedError("Stage 5: Report generation not yet implemented")

    async def list_templates(self) -> list[dict]:
        """List available report templates."""
        raise NotImplementedError("Stage 5: Templates not yet implemented")
