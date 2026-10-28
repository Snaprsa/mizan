"""
Category 18: Data Quality and Governance Variables

Source tracking, verification status, and data quality metrics.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .enums import SourceType, VerificationStatus


class DataField(BaseModel):
    """Metadata for an individual data field."""
    field_name: str = Field(..., description="Name of the field")
    source: Optional[SourceType] = Field(default=None)
    source_detail: Optional[str] = Field(default=None)
    timestamp: Optional[datetime] = Field(default=None)
    verified: Optional[VerificationStatus] = Field(default=None)
    confidence: Optional[float] = Field(default=None, ge=0, le=1)
    notes: Optional[str] = Field(default=None)


class DataQuality(BaseModel):
    """
    Data quality and governance variables.
    
    Tracking data provenance, verification status, and quality metrics
    for transparency and audit purposes.
    """
    
    # Overall Quality Scores
    overall_data_quality_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Overall data quality score"
    )
    completeness_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Data completeness score"
    )
    accuracy_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Data accuracy score"
    )
    timeliness_score: Optional[int] = Field(
        default=None, ge=0, le=100,
        description="Data timeliness score"
    )
    
    # Source Information
    primary_data_sources: Optional[list[str]] = Field(
        default=None,
        description="Primary data sources used"
    )
    data_sources_count: Optional[int] = Field(
        default=None, ge=0,
        description="Number of data sources consulted"
    )
    owner_provided_data: Optional[bool] = Field(
        default=None,
        description="Whether owner provided data"
    )
    broker_provided_data: Optional[bool] = Field(
        default=None,
        description="Whether broker provided data"
    )
    public_registry_data: Optional[bool] = Field(
        default=None,
        description="Whether public registry data was used"
    )
    
    # Verification
    verification_level: Optional[str] = Field(
        default=None,
        description="Level of verification (desktop, enhanced, comprehensive)"
    )
    site_inspection_completed: Optional[bool] = Field(default=None)
    site_inspection_date: Optional[str] = Field(default=None)
    documents_reviewed: Optional[list[str]] = Field(
        default=None,
        description="List of documents reviewed"
    )
    third_party_reports: Optional[list[str]] = Field(
        default=None,
        description="Third-party reports obtained"
    )
    
    # Field-Level Tracking
    field_metadata: Optional[list[DataField]] = Field(
        default=None,
        description="Metadata for individual fields"
    )
    
    # Timestamps
    data_collection_date: Optional[datetime] = Field(default=None)
    data_cutoff_date: Optional[datetime] = Field(default=None)
    last_update_date: Optional[datetime] = Field(default=None)
    market_data_as_of: Optional[datetime] = Field(default=None)
    
    # Completeness
    fields_total: Optional[int] = Field(default=None, ge=0)
    fields_populated: Optional[int] = Field(default=None, ge=0)
    fields_verified: Optional[int] = Field(default=None, ge=0)
    missing_critical_fields: Optional[list[str]] = Field(default=None)
    
    # Confidence
    value_confidence_interval_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Confidence interval on value estimate (±%)"
    )
    value_range_low_sar: Optional[float] = Field(default=None, ge=0)
    value_range_high_sar: Optional[float] = Field(default=None, ge=0)
    confidence_level_pct: Optional[float] = Field(
        default=None, ge=0, le=100,
        description="Statistical confidence level"
    )
    
    # Quality Flags
    has_outliers: Optional[bool] = Field(default=None)
    outlier_fields: Optional[list[str]] = Field(default=None)
    data_inconsistencies: Optional[list[str]] = Field(default=None)
    red_flags: Optional[list[str]] = Field(default=None)
    
    # Cleaning and Processing
    cleaning_rules_applied: Optional[list[str]] = Field(default=None)
    imputed_fields: Optional[list[str]] = Field(default=None)
    imputation_methods: Optional[dict] = Field(default=None)
    
    # Version Control
    model_version: Optional[str] = Field(default=None)
    schema_version: Optional[str] = Field(default=None)
    valuation_version: Optional[int] = Field(default=None, ge=1)
    previous_valuation_date: Optional[str] = Field(default=None)
    previous_value_sar: Optional[float] = Field(default=None, ge=0)
    value_change_pct: Optional[float] = Field(default=None)
    
    # Audit Trail
    prepared_by: Optional[str] = Field(default=None)
    reviewed_by: Optional[str] = Field(default=None)
    approved_by: Optional[str] = Field(default=None)
    valuer_qualification: Optional[str] = Field(default=None)
    valuer_license_number: Optional[str] = Field(default=None)
    
    # Limitations
    scope_limitations: Optional[list[str]] = Field(default=None)
    data_limitations: Optional[list[str]] = Field(default=None)
    methodology_limitations: Optional[list[str]] = Field(default=None)
    caveats: Optional[list[str]] = Field(default=None)

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "overall_data_quality_score": 85,
                "completeness_score": 90,
                "verification_level": "enhanced",
                "site_inspection_completed": True,
                "value_confidence_interval_pct": 10,
            }
        }
