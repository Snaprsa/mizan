"""
Category 1: Asset Identity and Scope

Defines the purpose, value definition, interest valued, and key dates
for the valuation engagement.
"""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from .enums import ValuationPurpose, ValueDefinition, InterestValued, ValuationStandard


class AssetIdentity(BaseModel):
    """
    Asset identity and scope variables.
    
    Captures the fundamental parameters of the valuation assignment including
    purpose, value definition, interest type, and key dates.
    """
    
    # Purpose and Value Definition
    valuation_purpose: Optional[ValuationPurpose] = Field(
        default=None,
        description="Purpose of valuation (sale, financing, tax, reporting, litigation, internal)"
    )
    value_definition: Optional[ValueDefinition] = Field(
        default=None,
        description="Type of value (market, investment, fair, insurable, liquidation)"
    )
    interest_valued: Optional[InterestValued] = Field(
        default=None,
        description="Interest being valued (fee simple, leased fee, leasehold, partial, strata, usufruct)"
    )
    
    # Key Dates
    effective_date: Optional[date] = Field(
        default=None,
        description="Effective date of valuation"
    )
    inspection_date: Optional[date] = Field(
        default=None,
        description="Date of property inspection"
    )
    report_date: Optional[date] = Field(
        default=None,
        description="Date of valuation report"
    )
    
    # Standards and Assumptions
    valuation_standard: Optional[ValuationStandard] = Field(
        default=None,
        description="Valuation standard (IVS, RICS Red Book, USPAP, TAQEEM, local)"
    )
    assumptions: Optional[list[str]] = Field(
        default=None,
        description="General assumptions made in the valuation"
    )
    special_assumptions: Optional[list[str]] = Field(
        default=None,
        description="Special assumptions (vacant possession, stabilized occupancy, as-is, as-complete)"
    )
    
    # Data Sources
    data_sources: Optional[list[str]] = Field(
        default=None,
        description="Data sources used in the valuation"
    )
    data_cutoff_date: Optional[date] = Field(
        default=None,
        description="Cut-off date for market data"
    )
    verification_level: Optional[str] = Field(
        default=None,
        description="Level of data verification performed"
    )
    
    # Report Identifiers
    report_reference: Optional[str] = Field(
        default=None,
        description="Unique report reference number"
    )
    client_name: Optional[str] = Field(
        default=None,
        description="Client requesting the valuation"
    )
    intended_users: Optional[list[str]] = Field(
        default=None,
        description="Intended users of the valuation"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "valuation_purpose": "financing",
                "value_definition": "market_value",
                "interest_valued": "fee_simple",
                "effective_date": "2025-01-14",
                "valuation_standard": "taqeem",
            }
        }
