"""
Domain enums for Saudi real estate valuation platform.
Shared across all modules — API, extractors, workers, reporting.
"""

from enum import Enum


# === Property ===

class PropertyType(str, Enum):
    # Land
    RAW_LAND = "raw_land"
    SERVICED_LAND = "serviced_land"
    # Residential
    VILLA = "villa"
    APARTMENT = "apartment"
    COMPOUND = "compound"
    BRANDED_RESIDENCE = "branded_residence"
    TOWNHOUSE = "townhouse"
    DUPLEX = "duplex"
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
    SPECIAL_PURPOSE = "special_purpose"
    OTHER = "other"
    UNKNOWN = "unknown"


class DealType(str, Enum):
    SALE = "sale"
    LEASE = "lease"
    RENT = "rent"
    UNKNOWN = "unknown"


class EvidenceType(str, Enum):
    """Listing vs actual transaction — critical distinction."""
    LISTING_ASKING = "listing_asking"         # Asking price, not achieved
    TRANSACTION_ACHIEVED = "transaction_achieved"  # Confirmed deal
    OFFER_ACCEPTED = "offer_accepted"         # Offer but not closed
    AUCTION_RESULT = "auction_result"
    OFFICIAL_RECORD = "official_record"       # Government / MOJ record
    UNKNOWN = "unknown"


class AreaType(str, Enum):
    """Different area measurements — sources are often inconsistent."""
    LAND_AREA = "land_area"       # Plot / land area
    PLOT_AREA = "plot_area"       # Synonym for land in some contexts
    BUA = "bua"                   # Built-up area
    GLA = "gla"                   # Gross leasable area
    NLA = "nla"                   # Net leasable area
    TOTAL_AREA = "total_area"     # Unspecified total
    OTHER = "other"
    UNKNOWN = "unknown"


class AreaUnit(str, Enum):
    SQM = "sqm"
    SQFT = "sqft"


class Currency(str, Enum):
    SAR = "SAR"
    USD = "USD"
    AED = "AED"
    OTHER = "OTHER"


class Tenure(str, Enum):
    FREEHOLD = "freehold"
    LEASEHOLD = "leasehold"
    GROUND_LEASE = "ground_lease"
    USUFRUCT = "usufruct"           # حق الانتفاع
    MUSATAHA = "musataha"           # حق المساطحة
    UNKNOWN = "unknown"


# === Source & Extraction ===

class SourceType(str, Enum):
    URL = "url"
    PDF = "pdf"
    MANUAL = "manual"


class ExtractionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"           # Some fields extracted, others failed


class ComparableStatus(str, Enum):
    ACTIVE = "active"
    INVALID = "invalid"           # User marked as not usable
    OUTLIER = "outlier"           # User flagged as statistical outlier
    DRAFT = "draft"               # Extraction done, not yet reviewed


class ReliabilityScore(int, Enum):
    """Evidence reliability scale for KSA real estate."""
    AUTHENTICATED_TRANSACTION = 5   # Contract / official record / MOJ
    OFFICIAL_FILING = 4             # Regulatory disclosure / Ejar
    BROKER_MATERIAL = 3             # Broker PDF / agency listing
    MARKETPLACE_LISTING = 2         # Aqar, Pasteah, etc.
    USER_ENTERED = 1                # Manual / unverified


# === Case & Workflow ===

class CaseStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class DataClassification(str, Enum):
    """Fact/Assumption/Judgment tagging for auditability."""
    FACT = "fact"               # Directly from source with citation
    ASSUMPTION = "assumption"   # Requires human confirmation
    JUDGMENT = "judgment"       # Human valuation decision


# === Roles ===

class UserRole(str, Enum):
    ADMIN = "admin"
    VALUER = "valuer"           # Licensed valuer / appraiser
    ANALYST = "analyst"         # Data analyst / researcher
    REVIEWER = "reviewer"       # QA / senior review
    VIEWER = "viewer"           # Read-only access
