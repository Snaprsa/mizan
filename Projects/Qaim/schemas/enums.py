"""Shared enumerations for the Qaim platform."""
from enum import Enum


class PropertyCategory(str, Enum):
    LAND = "land"
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    HOSPITALITY = "hospitality"
    INDUSTRIAL = "industrial"
    SPECIAL_PURPOSE = "special_purpose"


class PropertySubType(str, Enum):
    # Land
    RAW_LAND = "raw_land"
    SERVICED_LAND = "serviced_land"
    # Residential
    VILLA = "villa"
    APARTMENT = "apartment"
    COMPOUND = "compound"
    BRANDED_RESIDENCE = "branded_residence"
    # Commercial
    OFFICE = "office"
    RETAIL = "retail"
    MIXED_USE = "mixed_use"
    # Hospitality
    HOTEL = "hotel"
    SERVICED_APARTMENT = "serviced_apartment"
    # Industrial
    WAREHOUSE = "warehouse"
    LOGISTICS = "logistics"
    FACTORY = "factory"
    # Special
    OTHER = "other"


class TenureType(str, Enum):
    FREEHOLD = "freehold"
    LEASEHOLD = "leasehold"
    GROUND_LEASE = "ground_lease"
    USUFRUCT = "usufruct"
    MUSATAHA = "musataha"
    UNKNOWN = "unknown"


class AreaType(str, Enum):
    PLOT_AREA = "plot_area"
    LAND_AREA = "land_area"
    BUA = "bua"  # Built-Up Area
    GLA = "gla"  # Gross Leasable Area
    NLA = "nla"  # Net Leasable Area
    OTHER = "other"


class AreaUnit(str, Enum):
    SQM = "sqm"
    SQFT = "sqft"


class Currency(str, Enum):
    SAR = "SAR"
    USD = "USD"
    AED = "AED"
    OTHER = "other"


class EvidenceType(str, Enum):
    LISTING = "listing"
    TRANSACTION = "transaction"
    ASKING_PRICE = "asking_price"
    ACHIEVED_PRICE = "achieved_price"
    UNKNOWN = "unknown"


class SourceType(str, Enum):
    URL = "url"
    PDF = "pdf"
    MANUAL = "manual"


class ReliabilityScore(int, Enum):
    """1-5 scale for evidence reliability.
    1 = user-entered manual data
    2 = marketplace listing
    3 = broker brochure / PDF
    4 = official filing / regulatory disclosure
    5 = authenticated transaction / contract
    """
    USER_ENTERED = 1
    MARKETPLACE_LISTING = 2
    BROKER_MATERIAL = 3
    OFFICIAL_FILING = 4
    AUTHENTICATED_TRANSACTION = 5


class ExtractionJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class FactType(str, Enum):
    """Classification per the Fact/Assumption/Judgment rule."""
    FACT = "fact"          # Directly supported by source/citation
    ASSUMPTION = "assumption"  # Requires confirmation
    JUDGMENT = "judgment"  # Human valuation decision


class UserRole(str, Enum):
    ADMIN = "admin"
    VALUER = "valuer"
    REVIEWER = "reviewer"
    VIEWER = "viewer"
