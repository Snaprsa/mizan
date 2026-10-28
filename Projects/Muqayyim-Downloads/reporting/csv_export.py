"""
CSV export for comparables.
"""

import csv
import io
from typing import Any


# Column order for export
EXPORT_COLUMNS = [
    ("Source", "source_url"),
    ("Source Type", "source_type"),
    ("Status", "status"),
    ("Reliability", "reliability_score"),
    ("Title", "property_title"),
    ("City", "city"),
    ("District", "district"),
    ("Property Type", "property_type"),
    ("Evidence Type", "evidence_type"),
    ("Asking Price (SAR)", "asking_price"),
    ("Transacted Price (SAR)", "transacted_price"),
    ("Area (sqm)", "primary_area_sqm"),
    ("Price/sqm", "price_per_sqm"),
    ("Listing Date", "listing_date"),
    ("Transaction Date", "transaction_date"),
    ("Tenure", "tenure"),
    ("Latitude", "latitude"),
    ("Longitude", "longitude"),
    ("Notes", "notes"),
]


def generate_csv(case: Any, comps_with_fields: list[tuple]) -> io.BytesIO:
    """
    Generate CSV bytes from case comparables.

    Args:
        case: Case ORM object
        comps_with_fields: list of (Comparable, [ExtractedField], Source) tuples
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([col[0] for col in EXPORT_COLUMNS])

    # Data rows
    for comp, fields, source in comps_with_fields:
        row = []
        for label, attr in EXPORT_COLUMNS:
            if attr == "source_url":
                row.append(source.url if source else "")
            elif attr == "source_type":
                row.append(source.source_type if source else "")
            else:
                val = getattr(comp, attr, None)
                row.append(val if val is not None else "")
        writer.writerow(row)

    # Convert to bytes
    bytes_output = io.BytesIO(output.getvalue().encode("utf-8-sig"))  # BOM for Excel Arabic
    bytes_output.seek(0)
    return bytes_output
