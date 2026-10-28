"""Contracts for the map-first valuation workflow; rates are ratios, never percentages."""
from datetime import date
from typing import Literal
from pydantic import Field
from api.app.schemas.foundation import StrictModel


class StartAnalysis(StrictModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    property_type: str = Field(min_length=1, max_length=100)
    method: str
    name: str | None = Field(None, max_length=255)
    city: str | None = None
    district: str | None = None


class AnalysisValue(StrictModel):
    value: float = Field(strict=True)
    source: str = Field(min_length=1)
    as_of: date
    notes: str | None = None
    status: Literal['observed', 'market_derived', 'system_estimate', 'user_input', 'model_derived'] = 'user_input'


class SaveAnalysis(StrictModel):
    expected_revision: int = Field(ge=1)
    method: str
    inputs: dict[str, AnalysisValue] = Field(default_factory=dict, max_length=40)
    radius_km: float = Field(3, ge=0.1, le=50)
    lookback_days: int = Field(365, ge=1, le=3650)
    as_of: date


class RunAnalysis(StrictModel):
    expected_revision: int = Field(ge=1)
