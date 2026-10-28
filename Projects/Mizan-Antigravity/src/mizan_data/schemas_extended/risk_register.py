"""
Category 16: Risk Variables

Explicit risk register covering all risk categories.
"""

from typing import Optional

from pydantic import BaseModel, Field

from .enums import RiskLevel


class RiskItem(BaseModel):
    """Individual risk item."""
    risk_type: str = Field(..., description="Type of risk")
    description: Optional[str] = Field(default=None)
    probability: Optional[RiskLevel] = Field(default=None)
    impact: Optional[RiskLevel] = Field(default=None)
    mitigation: Optional[str] = Field(default=None)
    residual_risk: Optional[RiskLevel] = Field(default=None)


class RiskRegister(BaseModel):
    """
    Risk register variables.
    
    Comprehensive risk assessment covering market, leasing, construction,
    regulatory, environmental, and operational risks.
    """
    
    # Overall Risk Assessment
    overall_risk_rating: Optional[RiskLevel] = Field(
        default=None,
        description="Overall property risk rating"
    )
    risk_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Risk score 0-100"
    )
    risk_items: Optional[list[RiskItem]] = Field(
        default=None,
        description="Detailed risk register items"
    )
    
    # Market Risk
    market_risk_level: Optional[RiskLevel] = Field(default=None)
    market_risk_factors: Optional[list[str]] = Field(default=None)
    liquidity_risk_level: Optional[RiskLevel] = Field(default=None)
    cap_rate_expansion_risk: Optional[RiskLevel] = Field(default=None)
    cap_rate_volatility_pct: Optional[float] = Field(default=None, ge=0)
    price_decline_scenario_pct: Optional[float] = Field(default=None)
    
    # Leasing Risk
    leasing_risk_level: Optional[RiskLevel] = Field(default=None)
    tenant_default_risk: Optional[RiskLevel] = Field(default=None)
    concentration_risk: Optional[RiskLevel] = Field(default=None)
    top_tenant_risk_assessment: Optional[str] = Field(default=None)
    vacancy_risk: Optional[RiskLevel] = Field(default=None)
    lease_rollover_risk: Optional[RiskLevel] = Field(default=None)
    rent_decline_scenario_pct: Optional[float] = Field(default=None)
    
    # Construction Risk (for development)
    construction_risk_level: Optional[RiskLevel] = Field(default=None)
    contractor_risk: Optional[RiskLevel] = Field(default=None)
    cost_overrun_risk: Optional[RiskLevel] = Field(default=None)
    delay_risk: Optional[RiskLevel] = Field(default=None)
    construction_delay_scenario_months: Optional[int] = Field(default=None, ge=0)
    
    # Permitting Risk
    permitting_risk_level: Optional[RiskLevel] = Field(default=None)
    approval_probability_pct: Optional[float] = Field(default=None, ge=0, le=100)
    permit_delay_risk: Optional[RiskLevel] = Field(default=None)
    
    # Regulatory Risk
    regulatory_risk_level: Optional[RiskLevel] = Field(default=None)
    zoning_change_risk: Optional[RiskLevel] = Field(default=None)
    rent_control_risk: Optional[RiskLevel] = Field(default=None)
    building_code_change_risk: Optional[RiskLevel] = Field(default=None)
    regulatory_risk_factors: Optional[list[str]] = Field(default=None)
    
    # Title and Legal Risk
    title_risk_level: Optional[RiskLevel] = Field(default=None)
    legal_dispute_risk: Optional[RiskLevel] = Field(default=None)
    encumbrance_risk: Optional[RiskLevel] = Field(default=None)
    
    # Environmental Risk
    environmental_risk_level: Optional[RiskLevel] = Field(default=None)
    contamination_risk: Optional[RiskLevel] = Field(default=None)
    contamination_liability_sar: Optional[float] = Field(default=None, ge=0)
    
    # Climate Risk
    climate_physical_risk: Optional[RiskLevel] = Field(
        default=None,
        description="Physical climate risk (floods, storms, heat)"
    )
    climate_transition_risk: Optional[RiskLevel] = Field(
        default=None,
        description="Transition risk (stranded asset, regulation)"
    )
    energy_cost_increase_risk: Optional[RiskLevel] = Field(default=None)
    carbon_regulation_risk: Optional[RiskLevel] = Field(default=None)
    stranded_asset_risk: Optional[RiskLevel] = Field(default=None)
    climate_risk_factors: Optional[list[str]] = Field(default=None)
    
    # Operational Risk
    operational_risk_level: Optional[RiskLevel] = Field(default=None)
    staffing_risk: Optional[RiskLevel] = Field(default=None)
    systems_risk: Optional[RiskLevel] = Field(default=None)
    service_quality_risk: Optional[RiskLevel] = Field(default=None)
    
    # Reputation Risk
    reputation_risk: Optional[RiskLevel] = Field(default=None)
    brand_risk: Optional[RiskLevel] = Field(default=None)
    tenant_mix_risk: Optional[RiskLevel] = Field(default=None)
    
    # Country/FX Risk (for cross-border)
    country_risk_level: Optional[RiskLevel] = Field(default=None)
    country_risk_score: Optional[int] = Field(default=None, ge=0, le=100)
    fx_risk_level: Optional[RiskLevel] = Field(default=None)
    currency_exposure: Optional[str] = Field(default=None)
    repatriation_risk: Optional[RiskLevel] = Field(default=None)
    
    # Force Majeure
    force_majeure_risk_level: Optional[RiskLevel] = Field(default=None)
    force_majeure_assumptions: Optional[str] = Field(default=None)
    pandemic_impact_assessment: Optional[str] = Field(default=None)
    
    # Risk Mitigation
    risk_mitigation_strategies: Optional[list[str]] = Field(default=None)
    insurance_coverage_gaps: Optional[list[str]] = Field(default=None)
    key_risk_monitoring_indicators: Optional[list[str]] = Field(default=None)

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "overall_risk_rating": "moderate",
                "risk_score": 45,
                "market_risk_level": "moderate",
                "leasing_risk_level": "low",
            }
        }
