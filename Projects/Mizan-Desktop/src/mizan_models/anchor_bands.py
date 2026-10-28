"""
Anchor band computation for segment-based price bounds.

Computes price_per_sqm quantiles for each market segment to create
guardrails that keep predictions within plausible market ranges.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from mizan_data.schemas import CompRecord
from mizan_data.normalizers import create_segment_key, get_size_bucket

logger = logging.getLogger(__name__)

# Minimum sample size for reliable segment statistics
N_MIN = 10


@dataclass
class SegmentBounds:
    """Price bounds for a market segment."""

    segment_key: str
    count: int
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    mean: float
    std: float

    @property
    def is_reliable(self) -> bool:
        """Check if segment has enough samples for reliable bounds."""
        return self.count >= N_MIN


class AnchorBandBuilder:
    """
    Builds and stores anchor price bands by market segment.

    Segments are defined by: city, district, property_type, and optionally size_bucket.
    Provides fallback logic for segments with insufficient data.
    """

    def __init__(self, use_size_bucket: bool = False):
        """
        Initialize anchor band builder.

        Args:
            use_size_bucket: Whether to include size bucket in segment key
        """
        self.use_size_bucket = use_size_bucket
        self.bands: dict[str, SegmentBounds] = {}
        self.city_bands: dict[str, SegmentBounds] = {}
        self.property_type_bands: dict[str, SegmentBounds] = {}
        self.global_band: Optional[SegmentBounds] = None

    def fit(self, comps: list[CompRecord]) -> "AnchorBandBuilder":
        """
        Compute anchor bands from comparable sales.

        Args:
            comps: List of comparable sale records

        Returns:
            Self for chaining
        """
        df = self._comps_to_df(comps)

        # Compute segment-level bands (city|district|property_type)
        self._compute_segment_bands(df)

        # Compute city-level bands (for fallback)
        self._compute_city_bands(df)

        # Compute property-type-level bands (for fallback)
        self._compute_property_type_bands(df)

        # Compute global band (ultimate fallback)
        self._compute_global_band(df)

        logger.info(
            f"Computed anchor bands: {len(self.bands)} segments, "
            f"{len(self.city_bands)} cities, global n={self.global_band.count if self.global_band else 0}"
        )
        return self

    def _comps_to_df(self, comps: list[CompRecord]) -> pd.DataFrame:
        """Convert comp records to DataFrame."""
        records = []
        for comp in comps:
            rec = {
                "city": comp.city,
                "district": comp.district,
                "property_type": comp.property_type.value,
                "area_sqm": comp.area_sqm,
                "price_per_sqm": comp.price_per_sqm,
            }
            if self.use_size_bucket:
                rec["size_bucket"] = get_size_bucket(
                    comp.area_sqm, comp.property_type.value
                )
            records.append(rec)
        return pd.DataFrame(records)

    def _compute_segment_bands(self, df: pd.DataFrame) -> None:
        """Compute bands for each city|district|property_type segment."""
        group_cols = ["city", "district", "property_type"]
        if self.use_size_bucket:
            group_cols.append("size_bucket")

        for key, group in df.groupby(group_cols):
            if isinstance(key, tuple):
                if self.use_size_bucket:
                    city, district, prop_type, size_bucket = key
                    segment_key = create_segment_key(
                        city, district, prop_type, size_bucket
                    )
                else:
                    city, district, prop_type = key
                    segment_key = create_segment_key(city, district, prop_type)
            else:
                segment_key = str(key)

            self.bands[segment_key] = self._compute_quantiles(
                segment_key, group["price_per_sqm"]
            )

    def _compute_city_bands(self, df: pd.DataFrame) -> None:
        """Compute bands for each city|property_type combination."""
        for (city, prop_type), group in df.groupby(["city", "property_type"]):
            key = f"{city}|{prop_type}"
            self.city_bands[key] = self._compute_quantiles(key, group["price_per_sqm"])

    def _compute_property_type_bands(self, df: pd.DataFrame) -> None:
        """Compute bands for each property type (global)."""
        for prop_type, group in df.groupby("property_type"):
            self.property_type_bands[prop_type] = self._compute_quantiles(
                prop_type, group["price_per_sqm"]
            )

    def _compute_global_band(self, df: pd.DataFrame) -> None:
        """Compute global band across all data."""
        self.global_band = self._compute_quantiles("global", df["price_per_sqm"])

    def _compute_quantiles(self, key: str, prices: pd.Series) -> SegmentBounds:
        """Compute quantile statistics for a price series."""
        return SegmentBounds(
            segment_key=key,
            count=len(prices),
            p10=float(np.percentile(prices, 10)),
            p25=float(np.percentile(prices, 25)),
            p50=float(np.percentile(prices, 50)),
            p75=float(np.percentile(prices, 75)),
            p90=float(np.percentile(prices, 90)),
            mean=float(prices.mean()),
            std=float(prices.std()) if len(prices) > 1 else 0.0,
        )

    def get_bounds(
        self,
        city: str,
        district: str,
        property_type: str,
        area_sqm: Optional[float] = None,
    ) -> tuple[SegmentBounds, str]:
        """
        Get price bounds for a property, with fallback logic.

        Args:
            city: City name
            district: District name
            property_type: Property type
            area_sqm: Optional area for size bucket lookup

        Returns:
            Tuple of (SegmentBounds, fallback_level)
            - fallback_level: 'segment', 'city', 'property_type', or 'global'
        """
        # Try exact segment match
        if self.use_size_bucket and area_sqm:
            size_bucket = get_size_bucket(area_sqm, property_type)
            key = create_segment_key(city, district, property_type, size_bucket)
            if key in self.bands and self.bands[key].is_reliable:
                return self.bands[key], "segment"

        # Try segment without size bucket
        key = create_segment_key(city, district, property_type)
        if key in self.bands and self.bands[key].is_reliable:
            return self.bands[key], "segment"

        # Fallback to city level
        city_key = f"{city}|{property_type}"
        if city_key in self.city_bands and self.city_bands[city_key].is_reliable:
            return self.city_bands[city_key], "city"

        # Fallback to property type level
        if (
            property_type in self.property_type_bands
            and self.property_type_bands[property_type].is_reliable
        ):
            return self.property_type_bands[property_type], "property_type"

        # Ultimate fallback to global
        if self.global_band:
            return self.global_band, "global"

        raise ValueError("No anchor bands available")

    def to_dataframe(self) -> pd.DataFrame:
        """Export all segment bands to DataFrame."""
        records = []
        for key, bounds in self.bands.items():
            records.append(
                {
                    "segment_key": key,
                    "level": "segment",
                    "count": bounds.count,
                    "p10": bounds.p10,
                    "p25": bounds.p25,
                    "p50": bounds.p50,
                    "p75": bounds.p75,
                    "p90": bounds.p90,
                    "mean": bounds.mean,
                    "std": bounds.std,
                }
            )
        for key, bounds in self.city_bands.items():
            records.append(
                {
                    "segment_key": key,
                    "level": "city",
                    "count": bounds.count,
                    "p10": bounds.p10,
                    "p25": bounds.p25,
                    "p50": bounds.p50,
                    "p75": bounds.p75,
                    "p90": bounds.p90,
                    "mean": bounds.mean,
                    "std": bounds.std,
                }
            )
        return pd.DataFrame(records)

    def save(self, filepath: str) -> None:
        """Save anchor bands to parquet file."""
        df = self.to_dataframe()
        df.to_parquet(filepath, index=False)
        logger.info(f"Saved anchor bands to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "AnchorBandBuilder":
        """Load anchor bands from parquet file."""
        df = pd.read_parquet(filepath)
        builder = cls()

        for _, row in df.iterrows():
            bounds = SegmentBounds(
                segment_key=row["segment_key"],
                count=int(row["count"]),
                p10=row["p10"],
                p25=row["p25"],
                p50=row["p50"],
                p75=row["p75"],
                p90=row["p90"],
                mean=row["mean"],
                std=row["std"],
            )
            if row["level"] == "segment":
                builder.bands[row["segment_key"]] = bounds
            elif row["level"] == "city":
                builder.city_bands[row["segment_key"]] = bounds

        logger.info(f"Loaded anchor bands from {filepath}")
        return builder


def get_segment_bounds(
    anchor_bands: AnchorBandBuilder,
    city: str,
    district: str,
    property_type: str,
    area_sqm: Optional[float] = None,
) -> tuple[float, float, float]:
    """
    Convenience function to get (p10, p50, p90) bounds.

    Returns:
        Tuple of (low_bound, mid_bound, high_bound) in price_per_sqm
    """
    bounds, _ = anchor_bands.get_bounds(city, district, property_type, area_sqm)
    return bounds.p10, bounds.p50, bounds.p90
