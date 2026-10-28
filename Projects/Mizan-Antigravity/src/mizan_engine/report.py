"""
Valuation Report Generator.

Creates professional valuation reports following TAQEEM/IVS standards.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from mizan_data.schemas import SubjectProperty
from mizan_data.schemas_extended import (
    ValuationPurpose,
    ValueDefinition,
    ValuationStandard,
)
from .approaches.base import ApproachResult
from .reconciliation import ReconciliationResult


logger = logging.getLogger(__name__)


@dataclass
class ValuationReport:
    """
    Professional valuation report.
    
    Follows TAQEEM (Saudi) and IVS (International) valuation standards.
    """
    
    # Report identification
    report_id: str
    effective_date: date
    report_date: date
    
    # Standards and scope
    purpose: ValuationPurpose = ValuationPurpose.FINANCING
    value_definition: ValueDefinition = ValueDefinition.MARKET_VALUE
    standard: ValuationStandard = ValuationStandard.TAQEEM
    
    # Subject property
    subject: Optional[SubjectProperty] = None
    property_description: str = ""
    
    # Approach results
    sales_comparison: Optional[ApproachResult] = None
    income_approach: Optional[ApproachResult] = None
    cost_approach: Optional[ApproachResult] = None
    
    # Reconciliation
    reconciliation: Optional[ReconciliationResult] = None
    
    # Final value
    final_value: float = 0
    value_range_low: float = 0
    value_range_high: float = 0
    confidence_score: int = 0
    
    # Metadata
    assumptions: list[str] = field(default_factory=list)
    limiting_conditions: list[str] = field(default_factory=list)
    valuer_name: str = ""
    valuer_license: str = ""
    
    def __post_init__(self):
        """Set final value from reconciliation if available."""
        if self.reconciliation and self.final_value == 0:
            self.final_value = self.reconciliation.final_value_mid
            self.value_range_low = self.reconciliation.final_value_low
            self.value_range_high = self.reconciliation.final_value_high
            self.confidence_score = self.reconciliation.confidence_score
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "report_id": self.report_id,
            "effective_date": self.effective_date.isoformat(),
            "report_date": self.report_date.isoformat(),
            "purpose": self.purpose.value if self.purpose else None,
            "value_definition": self.value_definition.value if self.value_definition else None,
            "standard": self.standard.value if self.standard else None,
            "subject": {
                "city": self.subject.city if self.subject else None,
                "district": self.subject.district if self.subject else None,
                "property_type": self.subject.property_type.value if self.subject else None,
                "area_sqm": self.subject.area_sqm if self.subject else None,
            },
            "property_description": self.property_description,
            "approaches": {
                "sales_comparison": self.sales_comparison.to_dict() if self.sales_comparison else None,
                "income": self.income_approach.to_dict() if self.income_approach else None,
                "cost": self.cost_approach.to_dict() if self.cost_approach else None,
            },
            "reconciliation": self.reconciliation.to_dict() if self.reconciliation else None,
            "final_value": int(self.final_value),
            "value_range": {
                "low": int(self.value_range_low),
                "high": int(self.value_range_high),
            },
            "confidence_score": self.confidence_score,
            "assumptions": self.assumptions,
            "limiting_conditions": self.limiting_conditions,
            "valuer": {
                "name": self.valuer_name,
                "license": self.valuer_license,
            },
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Export report as JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def summary(self) -> str:
        """Generate a text summary of the valuation."""
        lines = [
            f"VALUATION REPORT: {self.report_id}",
            f"{'=' * 50}",
            f"",
            f"Effective Date: {self.effective_date}",
            f"Purpose: {self.purpose.value if self.purpose else 'N/A'}",
            f"Standard: {self.standard.value if self.standard else 'N/A'}",
            f"",
            f"SUBJECT PROPERTY",
            f"-" * 30,
        ]
        
        if self.subject:
            lines.extend([
                f"Location: {self.subject.district}, {self.subject.city}",
                f"Type: {self.subject.property_type.value}",
                f"Area: {self.subject.area_sqm:,.0f} sqm",
            ])
        
        lines.extend([
            f"",
            f"VALUE INDICATION",
            f"-" * 30,
            f"Final Value: SAR {self.final_value:,.0f}",
            f"Range: SAR {self.value_range_low:,.0f} - {self.value_range_high:,.0f}",
            f"Confidence: {self.confidence_score}%",
            f"",
        ])
        
        if self.reconciliation:
            lines.append("APPROACH WEIGHTS")
            lines.append("-" * 30)
            for approach, weight in self.reconciliation.weights_used.items():
                result = self.reconciliation.approach_results.get(approach)
                if result:
                    lines.append(
                        f"{approach.value}: {weight*100:.0f}% → SAR {result.value_mid:,.0f}"
                    )
        
        return "\n".join(lines)


def create_report(
    subject: SubjectProperty,
    sales_result: Optional[ApproachResult] = None,
    income_result: Optional[ApproachResult] = None,
    cost_result: Optional[ApproachResult] = None,
    reconciliation: Optional[ReconciliationResult] = None,
    purpose: ValuationPurpose = ValuationPurpose.FINANCING,
) -> ValuationReport:
    """
    Create a valuation report from approach results.
    
    Args:
        subject: Subject property
        sales_result: Sales comparison result
        income_result: Income approach result
        cost_result: Cost approach result
        reconciliation: Reconciliation result
        purpose: Valuation purpose
        
    Returns:
        ValuationReport object
    """
    today = date.today()
    report_id = f"MZN-{today.strftime('%Y%m%d')}-{subject.city[:3].upper()}"
    
    return ValuationReport(
        report_id=report_id,
        effective_date=today,
        report_date=today,
        purpose=purpose,
        subject=subject,
        property_description=f"{subject.property_type.value} in {subject.district}, {subject.city}",
        sales_comparison=sales_result,
        income_approach=income_result,
        cost_approach=cost_result,
        reconciliation=reconciliation,
        assumptions=[
            "No hidden defects or structural issues",
            "All information provided is accurate",
            "Property complies with zoning regulations",
        ],
        limiting_conditions=[
            "Value based on current market conditions",
            "No detailed engineering inspection performed",
        ],
    )
