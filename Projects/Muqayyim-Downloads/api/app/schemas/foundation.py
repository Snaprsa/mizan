"""Explicit units, unknown values and provenance for progressively completed assets."""
from datetime import date
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False, str_strip_whitespace=True)


SITE_OUTLINE_NOTE = ('User-drawn outline on provider imagery. Approximate; not a certified cadastral, '
                     'title-deed or municipal boundary.')


class SiteOutline(StrictModel):
    """GeoJSON (RFC 7946) polygon. Positions are [longitude, latitude], unlike map records."""
    type: Literal['Polygon'] = 'Polygon'
    coordinates: list[list[list[float]]] = Field(min_length=1, max_length=1)
    source: Literal['user_drawn'] = 'user_drawn'
    cadastral: Literal[False] = False
    drawn_on: date
    basemap: str | None = Field(None, max_length=50)
    approximate_area_sqm: float | None = Field(None, gt=0)
    note: str = SITE_OUTLINE_NOTE

    @model_validator(mode='after')
    def valid_ring(self):
        ring = self.coordinates[0]
        if len(ring) < 4 or len(ring) > 500:
            raise ValueError('An outline ring needs between 3 and 499 distinct vertices')
        for position in ring:
            if len(position) != 2:
                raise ValueError('GeoJSON positions must be [longitude, latitude]')
            lng, lat = position
            if not (-180 <= lng <= 180 and -90 <= lat <= 90):
                raise ValueError('GeoJSON positions must be [longitude, latitude] within valid ranges')
        if ring[0] != ring[-1]:
            raise ValueError('A GeoJSON polygon ring must be closed (first position repeated last)')
        return self


class Location(StrictModel):
    address: str | None = None
    city: str | None = None
    district: str | None = None
    municipality: str | None = None
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    plot_number: str | None = None
    block_number: str | None = None
    plan_number: str | None = None
    # How the coordinates were obtained; precision is never upgraded beyond what the source supports.
    coordinate_source: Literal['map_pin', 'coordinate_entry', 'geocoded', 'imported', 'manual'] | None = None
    coordinate_precision: Literal['user_selected', 'rooftop', 'range_interpolated', 'geometric_center',
                                  'approximate'] | None = None
    site_outline: SiteOutline | None = None

    @model_validator(mode='after')
    def coordinates(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError('Latitude and longitude must be provided together')
        return self


class Land(StrictModel):
    area_sqm: float | None = Field(None, gt=0)
    width_m: float | None = Field(None, gt=0)
    depth_m: float | None = Field(None, gt=0)
    frontage_m: float | None = Field(None, ge=0)
    street_width_m: float | None = Field(None, ge=0)
    street_frontages: int | None = Field(None, ge=0)
    corner: bool | None = None
    shape: str | None = None
    topography: str | None = None
    orientation: str | None = None
    utilities: list[str] = Field(default_factory=list)


class Planning(StrictModel):
    land_use: str | None = None
    permitted_use: list[str] = Field(default_factory=list)
    far: float | None = Field(None, ge=0)
    coverage_ratio: float | None = Field(None, ge=0, le=1)
    height_limit_m: float | None = Field(None, ge=0)
    setbacks_m: dict[str, float] = Field(default_factory=dict)
    parking_requirements: str | None = None
    restrictions: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def setbacks(self):
        if any(v < 0 for v in self.setbacks_m.values()):
            raise ValueError('Setbacks cannot be negative')
        return self


class Building(StrictModel):
    built_up_area_sqm: float | None = Field(None, ge=0)
    gfa_sqm: float | None = Field(None, ge=0)
    gla_sqm: float | None = Field(None, ge=0)
    nla_sqm: float | None = Field(None, ge=0)
    floors: int | None = Field(None, ge=0)
    units: int | None = Field(None, ge=0)
    year_built: int | None = Field(None, ge=1800, le=2200)
    age_years: float | None = Field(None, ge=0)
    condition: str | None = None
    occupancy_ratio: float | None = Field(None, ge=0, le=1)
    current_use: str | None = None
    floor_number: int | None = Field(None, ge=-5, le=200)  # The unit's floor; `floors` is the building's count.
    unit_position: Literal['rear', 'side', 'front', 'corner'] | None = None
    grade: Literal['C', 'B', 'A', 'A+'] | None = None
    grade_basis: Literal['assumed', 'observed'] | None = None  # A hypothetical grade stays labelled as assumed.


class Financial(StrictModel):
    asking_price_sar: float | None = Field(None, ge=0)
    purchase_price_sar: float | None = Field(None, ge=0)
    annual_rent_sar: float | None = Field(None, ge=0)
    rent_sar_sqm_year: float | None = Field(None, ge=0)
    operating_expenses_sar_year: float | None = Field(None, ge=0)
    noi_sar_year: float | None = None


class Provenance(StrictModel):
    source: str | None = None
    source_url: HttpUrl | None = None
    collected_on: date | None = None
    confidence: int | None = Field(None, ge=0, le=100)
    notes: str | None = None


AdjustmentFactor = Literal['conditions_of_sale', 'financing', 'market_conditions', 'location', 'size', 'frontage',
                           'street_width', 'corner', 'shape', 'condition', 'age', 'quality', 'occupancy',
                           'development_potential', 'zoning', 'floor', 'position', 'grade', 'other']


class AdjustmentLine(StrictModel):
    """One reviewer adjustment to one comparable, in SAR per m² of the comparable unless stated."""
    comparable_id: str = Field(min_length=1, max_length=120)
    factor: AdjustmentFactor
    basis: Literal['percent', 'sar_per_sqm', 'sar_total']
    amount: float
    rationale: str = Field(min_length=3, max_length=1000)
    source: str | None = Field(None, max_length=500)
    status: Literal['proposed', 'approved'] = 'proposed'

    @model_validator(mode='after')
    def bounded(self):
        if self.basis == 'percent' and not -0.9 <= self.amount <= 2:
            raise ValueError('Percentage adjustments must be between -90% and +200% (enter 0.10 for 10%)')
        return self


class TimeAdjustment(StrictModel):
    """Market-conditions rule: compound annual change applied from each sale date to the valuation date."""
    annual_rate: float = Field(ge=-0.5, le=0.5)
    source: str = Field(min_length=3, max_length=500)
    as_of: date
    status: Literal['proposed', 'approved'] = 'proposed'


class AdjustmentRule(StrictModel):
    """One reviewer-set rate applied to every comparable from the subject-vs-comparable difference."""
    factor: Literal['size', 'floor', 'position', 'grade', 'street_width', 'corner']
    percent: float = Field(ge=-0.5, le=0.5)  # Fraction per unit of difference; 0.01 = 1%.
    source: str = Field(min_length=3, max_length=500)
    status: Literal['proposed', 'approved'] = 'proposed'


class ComparableAttributes(StrictModel):
    """Reviewed structured details of a comparable. Unknown stays None and is never adjusted for."""
    floor: int | None = Field(None, ge=-5, le=200)
    position: Literal['rear', 'side', 'front', 'corner'] | None = None
    grade: Literal['C', 'B', 'A', 'A+'] | None = None
    street_width_m: float | None = Field(None, ge=0)
    corner: bool | None = None


class AdjustmentSetup(StrictModel):
    lines: list[AdjustmentLine] = Field(default_factory=list, max_length=500)
    rules: list[AdjustmentRule] = Field(default_factory=list, max_length=20)
    time: TimeAdjustment | None = None
    weighting: Literal['equal', 'inverse_gross_adjustment', 'manual'] = 'equal'
    manual_weights: dict[str, float] = Field(default_factory=dict)
    weighting_rationale: str | None = Field(None, max_length=1000)
    conclusion_basis: Literal['median', 'mean', 'weighted_mean', 'weighted_median'] = 'median'
    exclusions: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode='after')
    def consistent(self):
        if any(w < 0 for w in self.manual_weights.values()):
            raise ValueError('Comparable weights cannot be negative')
        if any(len(reason.strip()) < 3 for reason in self.exclusions.values()):
            raise ValueError('Every excluded comparable needs a reason')
        return self


class ValuationSetup(StrictModel):
    method: str | None = None
    radius_km: float = Field(3, ge=0.1, le=50)
    lookback_days: int = Field(365, ge=1, le=3650)
    as_of: date | None = None
    adjustments: AdjustmentSetup = Field(default_factory=AdjustmentSetup)


class PropertyInput(StrictModel):
    name: str = Field(min_length=1, max_length=255)
    case_id: UUID | None = None
    country: str = Field('SA', pattern=r'^[A-Z]{2}$')
    currency: str = Field('SAR', pattern=r'^[A-Z]{3}$')
    locale: Literal['en-SA', 'ar-SA'] = 'en-SA'
    property_type: str | None = Field(None, max_length=100)
    location: Location = Field(default_factory=Location)
    land: Land = Field(default_factory=Land)
    planning: Planning = Field(default_factory=Planning)
    building: Building = Field(default_factory=Building)
    financial: Financial = Field(default_factory=Financial)
    provenance: Provenance = Field(default_factory=Provenance)
    analysis: ValuationSetup = Field(default_factory=ValuationSetup)

    @model_validator(mode='after')
    def currency_supported(self):
        # Financial keys explicitly denote SAR. Expand with currency-aware money fields later.
        if self.currency != 'SAR':
            raise ValueError('Only SAR financial inputs are currently implemented')
        return self


class PropertyUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=1)
    property: PropertyInput


class AssumptionInput(StrictModel):
    name: str = Field(min_length=1, max_length=255)
    value: float | str | bool
    unit: str = Field(min_length=1, max_length=50)
    category: str = Field(min_length=1, max_length=100)
    source: str = Field(min_length=1)
    as_of: date
    status: Literal['observed', 'market_derived', 'system_estimate', 'user_input', 'model_derived']
    user_override: float | str | bool | None = None
    notes: str | None = None

    @model_validator(mode='after')
    def override_reason(self):
        if self.user_override is not None and not self.notes:
            raise ValueError('An override requires explanatory notes')
        return self


class AssumptionUpdate(StrictModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=1)
    assumption: AssumptionInput


class CaseLink(StrictModel):
    case_id: UUID
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=1)


class SourceInput(StrictModel):
    name: str = Field(min_length=1, max_length=255)
    provider: str = Field(min_length=1, max_length=100)
    source_type: Literal['official_dataset', 'broker', 'listing_portal', 'user_upload', 'internal', 'economic', 'construction', 'rental']
    uri: str | None = None
    notes: str | None = None


class ObservationInput(StrictModel):
    external_id: str = Field(min_length=1, max_length=255)
    observed_on: date
    country: str = Field('SA', pattern=r'^[A-Z]{2}$')
    city: str = Field(min_length=1, max_length=255)
    district: str | None = None
    property_type: str = Field(min_length=1, max_length=100)
    metric: str = Field(min_length=1, max_length=100)
    unit: str = Field(min_length=1, max_length=50)
    raw_value: float | str | bool
    normalized_value: float | str | bool
    reliability: int = Field(ge=0, le=100)
    metadata: dict = Field(default_factory=dict)


class ObservationBatch(StrictModel):
    observations: list[ObservationInput] = Field(min_length=1, max_length=1000)
