"""
Enumeration types for valuation schemas.

Contains all enum definitions used across the 18 valuation categories.
"""

from enum import Enum


class ValuationPurpose(str, Enum):
    """Purpose of the valuation."""
    SALE = "sale"
    FINANCING = "financing"
    TAX = "tax"
    REPORTING = "reporting"
    LITIGATION = "litigation"
    INTERNAL = "internal"
    INSURANCE = "insurance"
    ACQUISITION = "acquisition"
    DISPOSAL = "disposal"


class ValueDefinition(str, Enum):
    """Type of value being estimated."""
    MARKET_VALUE = "market_value"
    INVESTMENT_VALUE = "investment_value"
    FAIR_VALUE = "fair_value"
    INSURABLE_VALUE = "insurable_value"
    LIQUIDATION_VALUE = "liquidation_value"
    GOING_CONCERN_VALUE = "going_concern_value"
    SYNERGISTIC_VALUE = "synergistic_value"


class InterestValued(str, Enum):
    """Type of property interest being valued."""
    FEE_SIMPLE = "fee_simple"
    LEASED_FEE = "leased_fee"
    LEASEHOLD = "leasehold"
    PARTIAL_INTEREST = "partial_interest"
    AIR_RIGHTS = "air_rights"
    STRATA = "strata"
    USUFRUCT = "usufruct"
    GROUND_LEASE = "ground_lease"


class ValuationStandard(str, Enum):
    """Valuation standard being followed."""
    IVS = "ivs"  # International Valuation Standards
    RICS = "rics"  # RICS Red Book
    USPAP = "uspap"  # US standards
    TAQEEM = "taqeem"  # Saudi Arabia
    LOCAL = "local"  # Local jurisdiction standards


class ExtendedPropertyType(str, Enum):
    """Extended property type classification."""
    OFFICE = "office"
    RETAIL = "retail"
    MULTIFAMILY = "multifamily"
    APARTMENT = "apartment"
    VILLA = "villa"
    TOWNHOUSE = "townhouse"
    HOTEL = "hotel"
    INDUSTRIAL = "industrial"
    WAREHOUSE = "warehouse"
    LOGISTICS = "logistics"
    MIXED_USE = "mixed_use"
    LAND = "land"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    DATA_CENTER = "data_center"
    SPECIALIZED = "specialized"


class QualityTier(int, Enum):
    """Quality tier rating 1-5."""
    BASIC = 1
    STANDARD = 2
    GOOD = 3
    SUPERIOR = 4
    LUXURY = 5


class ConditionRating(str, Enum):
    """Physical condition rating."""
    POOR = "poor"
    FAIR = "fair"
    AVERAGE = "average"
    GOOD = "good"
    EXCELLENT = "excellent"


class RiskLevel(str, Enum):
    """Risk assessment level."""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class CertificationType(str, Enum):
    """Green building certification types."""
    LEED = "leed"
    BREEAM = "breeam"
    WELL = "well"
    MOSTADAM = "mostadam"  # Saudi green building
    ESTIDAMA = "estidama"  # UAE
    GSAS = "gsas"  # Gulf states
    GREEN_STAR = "green_star"
    FITWEL = "fitwel"


class LeaseType(str, Enum):
    """Type of lease structure."""
    GROSS = "gross"
    MODIFIED_GROSS = "modified_gross"
    NET = "net"
    DOUBLE_NET = "double_net"
    TRIPLE_NET = "triple_net"
    ABSOLUTE_NET = "absolute_net"


class EscalationType(str, Enum):
    """Rent escalation type."""
    FIXED = "fixed"
    CPI = "cpi"
    STEP_UP = "step_up"
    TURNOVER = "turnover"
    MARKET_REVIEW = "market_review"


class ObsolescenceType(str, Enum):
    """Type of obsolescence."""
    PHYSICAL = "physical"
    FUNCTIONAL = "functional"
    TECHNICAL = "technical"
    EXTERNAL = "external"
    ECONOMIC = "economic"


class SourceType(str, Enum):
    """Data source type for quality tracking."""
    PRIMARY = "primary"  # Direct from owner/agent
    BROKER = "broker"
    PUBLIC_REGISTRY = "public_registry"
    LISTING = "listing"
    SURVEY = "survey"
    ESTIMATED = "estimated"
    ASSUMED = "assumed"


class VerificationStatus(str, Enum):
    """Verification status of data."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PARTIALLY_VERIFIED = "partially_verified"
    CONTRADICTED = "contradicted"


class TerminalValueMethod(str, Enum):
    """Method for calculating terminal value in DCF."""
    DIRECT_CAP = "direct_cap"
    GORDON_GROWTH = "gordon_growth"
    RESIDUAL = "residual"
    MARKET_MULTIPLE = "market_multiple"


class HazardType(str, Enum):
    """Natural hazard types."""
    FLOOD = "flood"
    EARTHQUAKE = "earthquake"
    STORM = "storm"
    WILDFIRE = "wildfire"
    SUBSIDENCE = "subsidence"
    SANDSTORM = "sandstorm"
    EXTREME_HEAT = "extreme_heat"


class ZoningCategory(str, Enum):
    """Zoning category types."""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    MIXED_USE = "mixed_use"
    AGRICULTURAL = "agricultural"
    INSTITUTIONAL = "institutional"
    SPECIAL = "special"
