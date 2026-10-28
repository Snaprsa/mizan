"""
Category 15: Taxes, Fees, and Transaction Costs

Property taxes, transfer taxes, and transaction-related fees.
"""

from typing import Optional

from pydantic import BaseModel, Field


class TaxesFees(BaseModel):
    """
    Taxes, fees, and transaction cost variables.
    
    Tax liabilities, transfer costs, and transaction fees applicable
    to the property and its transaction.
    """
    
    # Property Taxes
    property_tax_annual_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Annual property tax"
    )
    property_tax_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Property tax rate"
    )
    tax_assessment_value_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Assessed value for tax purposes"
    )
    assessment_ratio: Optional[float] = Field(
        default=None, ge=0, le=1,
        description="Assessment ratio to market value"
    )
    tax_assessment_date: Optional[str] = Field(
        default=None,
        description="Date of last assessment"
    )
    tax_appeal_potential: Optional[bool] = Field(
        default=None,
        description="Whether tax assessment can be appealed"
    )
    
    # White Land Tax (Saudi-specific)
    white_land_tax_applicable: Optional[bool] = Field(
        default=None,
        description="Whether white land tax applies"
    )
    white_land_tax_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="White land tax rate"
    )
    white_land_tax_annual_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Annual white land tax"
    )
    
    # Transfer Taxes
    transfer_tax_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Transfer tax/stamp duty rate"
    )
    transfer_tax_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Transfer tax amount based on value"
    )
    stamp_duty_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Stamp duty"
    )
    registration_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Land registration fees"
    )
    
    # VAT
    vat_applicable: Optional[bool] = Field(
        default=None,
        description="Whether VAT applies to transaction"
    )
    vat_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="VAT rate"
    )
    vat_treatment: Optional[str] = Field(
        default=None,
        description="VAT treatment (exempt, zero-rated, standard)"
    )
    vat_on_rents: Optional[bool] = Field(
        default=None,
        description="Whether VAT applies to rental income"
    )
    
    # Withholding Taxes
    withholding_tax_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Withholding tax on income remittance"
    )
    withholding_tax_applicable: Optional[bool] = Field(
        default=None,
        description="Whether withholding tax applies"
    )
    
    # Zakat / Corporate Tax
    zakat_applicable: Optional[bool] = Field(
        default=None,
        description="Whether Zakat applies"
    )
    zakat_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Zakat rate"
    )
    corporate_tax_rate_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Corporate income tax rate"
    )
    tax_regime: Optional[str] = Field(
        default=None,
        description="Applicable tax regime"
    )
    
    # Municipality Fees
    municipality_fee_annual_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Annual municipality fees"
    )
    municipality_services_fee_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Municipality services fee"
    )
    waste_collection_fee_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Waste collection fee"
    )
    
    # Transaction Costs - Buyer Side
    buyer_legal_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Buyer's legal fees"
    )
    buyer_due_diligence_costs_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Due diligence costs"
    )
    buyer_valuation_fee_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Valuation fee"
    )
    buyer_brokerage_fee_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Buyer's brokerage fee percentage"
    )
    buyer_brokerage_fee_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Buyer's brokerage fee"
    )
    total_buyer_costs_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total buyer transaction costs"
    )
    buyer_costs_pct_of_price: Optional[float] = Field(
        default=None, ge=0,
        description="Buyer costs as % of price"
    )
    
    # Transaction Costs - Seller Side
    seller_legal_fees_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Seller's legal fees"
    )
    seller_brokerage_fee_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Seller's brokerage fee percentage"
    )
    seller_brokerage_fee_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Seller's brokerage fee"
    )
    total_seller_costs_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Total seller transaction costs"
    )
    seller_costs_pct_of_price: Optional[float] = Field(
        default=None, ge=0,
        description="Seller costs as % of price"
    )
    
    # Insurance
    property_insurance_annual_sar: Optional[float] = Field(
        default=None, ge=0,
        description="Annual property insurance premium"
    )
    insurance_tax_deductible: Optional[bool] = Field(
        default=None,
        description="Whether insurance is tax deductible"
    )
    
    # Tax Optimization
    tax_structure_notes: Optional[str] = Field(
        default=None,
        description="Notes on tax structure/optimization"
    )
    holding_company_jurisdiction: Optional[str] = Field(
        default=None,
        description="Holding company jurisdiction if applicable"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "property_tax_annual_sar": 50000,
                "transfer_tax_rate_pct": 5,
                "vat_applicable": True,
                "vat_rate_pct": 15,
                "total_buyer_costs_sar": 750000,
            }
        }
