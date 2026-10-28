"""
Data loading utilities for CSV files.

Handles loading, validation, and conversion of comps and subject properties
from CSV format into validated Pydantic models.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from pydantic import ValidationError

from .normalizers import normalize_city, normalize_district
from .schemas import CompRecord, SubjectProperty

logger = logging.getLogger(__name__)


def load_comps(
    filepath: str | Path,
    validate: bool = True,
    skip_invalid: bool = True,
) -> tuple[list[CompRecord], list[dict]]:
    """
    Load comparable sales from CSV file.

    Args:
        filepath: Path to comps.csv file
        validate: Whether to validate each record with Pydantic
        skip_invalid: If True, skip invalid records; if False, raise on first error

    Returns:
        Tuple of (valid_records, invalid_records)
        - valid_records: List of validated CompRecord objects
        - invalid_records: List of dicts with 'row' and 'error' keys

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If validate=True, skip_invalid=False, and validation fails
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Comps file not found: {filepath}")

    logger.info(f"Loading comps from {filepath}")
    df = pd.read_csv(filepath)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Handle date parsing
    if "trans_date" in df.columns:
        df["trans_date"] = pd.to_datetime(df["trans_date"]).dt.date

    # Normalize city and district
    if "city" in df.columns:
        df["city"] = df["city"].apply(normalize_city)
    if "district" in df.columns:
        df["district"] = df["district"].apply(normalize_district)

    valid_records = []
    invalid_records = []

    for idx, row in df.iterrows():
        row_dict = row.dropna().to_dict()

        if not validate:
            # Just convert to dict without validation
            valid_records.append(CompRecord.model_construct(**row_dict))
            continue

        try:
            record = CompRecord(**row_dict)
            valid_records.append(record)
        except ValidationError as e:
            error_info = {"row": int(idx), "data": row_dict, "error": str(e)}
            if not skip_invalid:
                raise ValueError(f"Validation failed at row {idx}: {e}") from e
            invalid_records.append(error_info)
            logger.warning(f"Skipping invalid row {idx}: {e}")

    logger.info(
        f"Loaded {len(valid_records)} valid records, "
        f"{len(invalid_records)} invalid records"
    )
    return valid_records, invalid_records


def load_subjects(
    filepath: str | Path,
    validate: bool = True,
    skip_invalid: bool = True,
) -> tuple[list[SubjectProperty], list[dict]]:
    """
    Load subject properties from CSV file.

    Args:
        filepath: Path to subject_properties.csv file
        validate: Whether to validate each record with Pydantic
        skip_invalid: If True, skip invalid records; if False, raise on first error

    Returns:
        Tuple of (valid_records, invalid_records)

    Raises:
        FileNotFoundError: If file does not exist
        ValueError: If validate=True, skip_invalid=False, and validation fails
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Subject properties file not found: {filepath}")

    logger.info(f"Loading subject properties from {filepath}")
    df = pd.read_csv(filepath)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Normalize city and district
    if "city" in df.columns:
        df["city"] = df["city"].apply(normalize_city)
    if "district" in df.columns:
        df["district"] = df["district"].apply(normalize_district)

    valid_records = []
    invalid_records = []

    for idx, row in df.iterrows():
        row_dict = row.dropna().to_dict()

        # Add property_id if not present
        if "property_id" not in row_dict:
            row_dict["property_id"] = f"SUBJ_{idx:04d}"

        if not validate:
            valid_records.append(SubjectProperty.model_construct(**row_dict))
            continue

        try:
            record = SubjectProperty(**row_dict)
            valid_records.append(record)
        except ValidationError as e:
            error_info = {"row": int(idx), "data": row_dict, "error": str(e)}
            if not skip_invalid:
                raise ValueError(f"Validation failed at row {idx}: {e}") from e
            invalid_records.append(error_info)
            logger.warning(f"Skipping invalid row {idx}: {e}")

    logger.info(
        f"Loaded {len(valid_records)} valid subjects, "
        f"{len(invalid_records)} invalid records"
    )
    return valid_records, invalid_records


def comps_to_dataframe(comps: list[CompRecord]) -> pd.DataFrame:
    """
    Convert list of CompRecord objects to pandas DataFrame.

    Args:
        comps: List of validated CompRecord objects

    Returns:
        DataFrame with all comp data plus computed columns
    """
    records = [comp.model_dump() for comp in comps]
    df = pd.DataFrame(records)

    # Add computed columns
    df["price_per_sqm"] = df["total_price_sar"] / df["area_sqm"]
    df["computed_age_years"] = df.apply(
        lambda row: row["age_years"]
        if pd.notna(row["age_years"])
        else (2024 - row["year_built"] if pd.notna(row["year_built"]) else 5),
        axis=1,
    )

    return df


def subjects_to_dataframe(subjects: list[SubjectProperty]) -> pd.DataFrame:
    """
    Convert list of SubjectProperty objects to pandas DataFrame.

    Args:
        subjects: List of validated SubjectProperty objects

    Returns:
        DataFrame with all subject data
    """
    records = [subj.model_dump() for subj in subjects]
    return pd.DataFrame(records)
