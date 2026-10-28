"""
Comprehensive valuation schemas package.

This package contains modular Pydantic schemas for professional real estate
valuation, organized into 18 categories following international valuation
standards (IVS, RICS Red Book, USPAP, TAQEEM).
"""

from .enums import (
    ValuationPurpose,
    ValueDefinition,
    InterestValued,
    ValuationStandard,
    ExtendedPropertyType,
    QualityTier,
    ConditionRating,
    RiskLevel,
    CertificationType,
)

from .asset_identity import AssetIdentity
from .location_catchment import LocationCatchment
from .site_land import SiteLand
from .planning_controls import PlanningControls
from .building_improvements import BuildingImprovements
from .physical_condition import PhysicalCondition, CapexItem
from .legal_title import LegalTitle
from .tenancy_leases import TenancyLeases, TenantRecord
from .operating_statements import OperatingStatements
from .market_evidence import MarketEvidence, SalesComparable, RentalComparable
from .cost_replacement import CostReplacement
from .development_residual import DevelopmentResidual
from .income_dcf import IncomeDCF
from .financing_capital import FinancingCapital
from .taxes_fees import TaxesFees
from .risk_register import RiskRegister, RiskItem
from .esg_sustainability import ESGSustainability
from .data_quality import DataQuality, DataField

__all__ = [
    # Enums
    "ValuationPurpose",
    "ValueDefinition",
    "InterestValued",
    "ValuationStandard",
    "ExtendedPropertyType",
    "QualityTier",
    "ConditionRating",
    "RiskLevel",
    "CertificationType",
    # Schema classes
    "AssetIdentity",
    "LocationCatchment",
    "SiteLand",
    "PlanningControls",
    "BuildingImprovements",
    "PhysicalCondition",
    "CapexItem",
    "LegalTitle",
    "TenancyLeases",
    "TenantRecord",
    "OperatingStatements",
    "MarketEvidence",
    "SalesComparable",
    "RentalComparable",
    "CostReplacement",
    "DevelopmentResidual",
    "IncomeDCF",
    "FinancingCapital",
    "TaxesFees",
    "RiskRegister",
    "RiskItem",
    "ESGSustainability",
    "DataQuality",
    "DataField",
]
