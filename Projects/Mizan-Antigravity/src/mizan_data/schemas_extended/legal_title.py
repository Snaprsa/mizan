"""
Category 7: Legal, Title, and Constraints

Title, liens, easements, litigation, and insurance.
"""

from typing import Optional

from pydantic import BaseModel, Field


class LegalTitle(BaseModel):
    """
    Legal, title, and constraint variables.
    
    Ownership structure, encumbrances, legal constraints, and compliance status.
    """
    
    # Title and Ownership
    title_type: Optional[str] = Field(
        default=None,
        description="Type of title (freehold, leasehold, etc.)"
    )
    ownership_structure: Optional[str] = Field(
        default=None,
        description="Ownership structure (individual, corporate, trust, etc.)"
    )
    registry_status: Optional[str] = Field(
        default=None,
        description="Land registry status"
    )
    title_deed_number: Optional[str] = Field(
        default=None,
        description="Title deed/instrument number"
    )
    title_insurance: Optional[bool] = Field(
        default=None,
        description="Whether title insurance is in place"
    )
    
    # Encumbrances
    has_liens: Optional[bool] = Field(
        default=None,
        description="Whether property has liens"
    )
    lien_details: Optional[list[str]] = Field(
        default=None,
        description="Details of any liens"
    )
    has_mortgages: Optional[bool] = Field(
        default=None,
        description="Whether mortgages are registered"
    )
    mortgage_amount_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total mortgage amount"
    )
    mortgage_holder: Optional[str] = Field(
        default=None,
        description="Mortgage holder/bank"
    )
    has_pledges: Optional[bool] = Field(
        default=None,
        description="Whether property is pledged"
    )
    
    # Easements and Restrictions
    has_easements: Optional[bool] = Field(
        default=None,
        description="Whether easements exist"
    )
    easement_types: Optional[list[str]] = Field(
        default=None,
        description="Types of easements"
    )
    easement_areas_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Total area affected by easements"
    )
    restrictive_covenants: Optional[list[str]] = Field(
        default=None,
        description="Restrictive covenants on the property"
    )
    deed_restrictions: Optional[list[str]] = Field(
        default=None,
        description="Deed restrictions"
    )
    
    # Boundary Issues
    has_encroachments: Optional[bool] = Field(
        default=None,
        description="Whether encroachments exist"
    )
    encroachment_details: Optional[str] = Field(
        default=None,
        description="Details of encroachments"
    )
    boundary_disputes: Optional[bool] = Field(
        default=None,
        description="Whether boundary disputes exist"
    )
    boundary_dispute_details: Optional[str] = Field(
        default=None,
        description="Details of any boundary disputes"
    )
    
    # Litigation
    active_litigation: Optional[bool] = Field(
        default=None,
        description="Whether there is active litigation"
    )
    litigation_details: Optional[str] = Field(
        default=None,
        description="Details of any litigation"
    )
    litigation_exposure_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Estimated litigation exposure"
    )
    pending_notices: Optional[list[str]] = Field(
        default=None,
        description="Pending legal notices"
    )
    code_violations: Optional[list[str]] = Field(
        default=None,
        description="Outstanding code violations"
    )
    code_violation_fines_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Fines for code violations"
    )
    
    # Insurance
    property_insurance_coverage_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Property insurance coverage amount"
    )
    liability_insurance_coverage_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Liability insurance coverage"
    )
    insurance_claims_history: Optional[str] = Field(
        default=None,
        description="Insurance claims history"
    )
    insurability_issues: Optional[bool] = Field(
        default=None,
        description="Whether there are insurability constraints"
    )
    insurance_exclusions: Optional[list[str]] = Field(
        default=None,
        description="Insurance exclusions"
    )
    
    # Licenses and Permits
    operating_licenses: Optional[list[str]] = Field(
        default=None,
        description="Operating licenses held"
    )
    permits_current: Optional[bool] = Field(
        default=None,
        description="Whether all permits are current"
    )
    permit_expiry_dates: Optional[dict] = Field(
        default=None,
        description="Permit expiry dates by type"
    )
    
    # Condo/HOA
    is_strata_title: Optional[bool] = Field(
        default=None,
        description="Whether property is strata/condo title"
    )
    hoa_name: Optional[str] = Field(
        default=None,
        description="HOA/management company name"
    )
    hoa_bylaws_review: Optional[str] = Field(
        default=None,
        description="Summary of HOA bylaw review"
    )
    service_charge_sar_per_sqm: Optional[float] = Field(
        default=None, ge=0,
        description="Annual service charge per sqm"
    )
    special_assessments_pending: Optional[bool] = Field(
        default=None,
        description="Whether special assessments are pending"
    )
    hoa_reserve_fund_sar: Optional[float] = Field(
        default=None, ge=0,
        description="HOA reserve fund balance"
    )
    hoa_litigation: Optional[bool] = Field(
        default=None,
        description="Whether HOA is involved in litigation"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "title_type": "freehold",
                "ownership_structure": "corporate",
                "has_liens": False,
                "has_mortgages": True,
                "mortgage_amount_sar": 5000000,
            }
        }
