"""
CSV processing service using Pandas.
Handles parsing, validation, and bulk-creation of EquipmentData rows.

Numeric attribute columns are detected dynamically from the CSV —
the system no longer hard-codes flowrate / pressure / temperature.
"""

import numpy as np
import pandas as pd
from pandas.errors import EmptyDataError

from .models import EquipmentData, UploadHistory

# Only these two columns are truly required in every CSV.
REQUIRED_COLUMNS = {"equipment_name", "type"}

# Columns that are never treated as numeric attributes
NON_ATTRIBUTE_COLS = {"equipment_name", "type", "id", "user", "upload",
                       "timestamp", "equipment_type"}

# Legacy fixed-model columns that map directly to model FloatFields
LEGACY_FLOAT_FIELDS = {"flowrate", "pressure", "temperature"}


class CSVProcessingError(Exception):
    """Raised when the uploaded CSV cannot be processed."""
    pass


def _detect_numeric_columns(df):
    """Return sorted list of numeric attribute column names from a DataFrame."""
    numeric_cols = []
    for col in df.columns:
        if col in NON_ATTRIBUTE_COLS:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
    return sorted(numeric_cols)


def process_csv(file, user):
    """
    Parse an uploaded CSV file and insert validated rows into the database.

    Required columns:  equipment_name, type
    All other numeric columns are stored automatically as dynamic attributes.

    Returns:
        dict with keys: rows_imported, equipment_count, upload_id, numeric_columns
    Raises:
        CSVProcessingError on bad data.
    """
    try:
        df = pd.read_csv(file)
    except EmptyDataError:
        raise CSVProcessingError("The uploaded CSV file is empty.")
    except Exception as exc:
        raise CSVProcessingError(f"Failed to read CSV: {exc}")

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise CSVProcessingError(
            f"Missing required columns: {', '.join(sorted(missing))}. "
            f"Expected at minimum: equipment_name, type"
        )

    # Drop rows where equipment_name is NaN
    df = df.dropna(subset=["equipment_name"])
    if df.empty:
        raise CSVProcessingError("CSV contains no valid data rows after cleaning.")

    # Coerce every non-required column to numeric where possible
    for col in df.columns:
        if col not in REQUIRED_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    numeric_cols = _detect_numeric_columns(df)
    if not numeric_cols:
        raise CSVProcessingError(
            "No numeric attribute columns detected. "
            "Please include at least one numeric column besides equipment_name and type."
        )

    # Drop rows that have NaN in ALL numeric columns
    df = df.dropna(subset=numeric_cols, how="all")
    # Fill remaining NaN in numeric cols with 0
    df[numeric_cols] = df[numeric_cols].fillna(0.0)

    if df.empty:
        raise CSVProcessingError("No valid numeric values found in the CSV.")

    # Fill optional type column
    df["type"] = df["type"].fillna("")

    # Record upload history first so we can link rows to it
    upload = UploadHistory.objects.create(
        user=user,
        file_name=getattr(file, "name", "unknown.csv"),
        rows_imported=len(df),
        numeric_columns=numeric_cols,
    )

    # Build EquipmentData objects
    objects = []
    for _, row in df.iterrows():
        kwargs = dict(
            user=user,
            upload=upload,
            equipment_name=str(row["equipment_name"]).strip(),
            equipment_type=str(row["type"]).strip(),
        )
        # Populate legacy float fields if present in CSV
        for legacy in LEGACY_FLOAT_FIELDS:
            if legacy in numeric_cols:
                kwargs[legacy] = float(row[legacy])

        # Store ALL numeric attributes (including legacy ones) in JSON field
        attrs = {}
        for col in numeric_cols:
            attrs[col] = round(float(row[col]), 4)
        kwargs["numeric_attributes"] = attrs

        objects.append(EquipmentData(**kwargs))

    EquipmentData.objects.bulk_create(objects)

    # ── Keep only the 5 most recent uploads; delete older ones ──
    MAX_UPLOADS = 5
    recent_ids = list(
        UploadHistory.objects.filter(user=user)
        .order_by("-uploaded_at")
        .values_list("id", flat=True)[:MAX_UPLOADS]
    )
    if recent_ids:
        UploadHistory.objects.filter(user=user).exclude(id__in=recent_ids).delete()

    return {
        "rows_imported": len(objects),
        "equipment_count": df["equipment_name"].nunique(),
        "upload_id": upload.id,
        "numeric_columns": numeric_cols,
    }


def get_summary_stats(user, upload_id=None):
    """
    Return aggregated statistics for a user's equipment data.
    All numeric attributes are detected dynamically.

    Returns dict with:
        - total_records
        - numeric_columns: [col_name, ...]
        - equipment_list: [{name, type, count, avg: {col: val, ...}}, ...]
        - parameter_averages: {col: val, ...}
        - type_distribution: [{type, count}, ...]
    """
    qs = EquipmentData.objects.filter(user=user)
    if upload_id is not None:
        qs = qs.filter(upload_id=upload_id)

    if not qs.exists():
        return {
            "total_records": 0,
            "numeric_columns": [],
            "equipment_list": [],
            "parameter_averages": {},
            "type_distribution": [],
        }

    rows = list(qs.values("equipment_name", "equipment_type", "numeric_attributes"))

    # Discover the union of all numeric attribute keys across rows
    all_keys = set()
    for r in rows:
        if r["numeric_attributes"]:
            all_keys.update(r["numeric_attributes"].keys())
    numeric_columns = sorted(all_keys)

    # Build a flat DataFrame from the JSON attributes
    flat_rows = []
    for r in rows:
        flat = {
            "equipment_name": r["equipment_name"],
            "equipment_type": r["equipment_type"],
        }
        attrs = r["numeric_attributes"] or {}
        for col in numeric_columns:
            flat[col] = attrs.get(col, np.nan)
        flat_rows.append(flat)

    df = pd.DataFrame(flat_rows)

    # ── Per-equipment aggregation ──
    agg_dict = {col: "mean" for col in numeric_columns}
    agg_dict["equipment_name"] = "count"  # reuse for count
    equip_agg = (
        df.groupby(["equipment_name", "equipment_type"])
        .agg(**{
            **{f"avg_{col}": (col, "mean") for col in numeric_columns},
            "count": ("equipment_name", "count"),
        })
        .reset_index()
    )
    equip_agg = equip_agg.rename(columns={"equipment_name": "name", "equipment_type": "type"})

    # Build equipment_list as list of dicts with nested "avg" dict
    equipment_list = []
    for _, erow in equip_agg.iterrows():
        entry = {
            "name": erow["name"],
            "type": erow["type"],
            "count": int(erow["count"]),
            "avg": {},
        }
        for col in numeric_columns:
            val = erow[f"avg_{col}"]
            entry["avg"][col] = round(float(val), 2) if pd.notna(val) else 0.0
        equipment_list.append(entry)

    # ── Overall parameter averages ──
    parameter_averages = {}
    for col in numeric_columns:
        val = df[col].mean()
        parameter_averages[col] = round(float(val), 2) if pd.notna(val) else 0.0

    # ── Type distribution (count per equipment_type) — UNCHANGED logic ──
    type_dist = (
        df.groupby("equipment_type")
        .size()
        .reset_index(name="count")
        .rename(columns={"equipment_type": "type"})
        .sort_values("count", ascending=False)
    )

    return {
        "total_records": len(df),
        "numeric_columns": numeric_columns,
        "equipment_list": equipment_list,
        "parameter_averages": parameter_averages,
        "type_distribution": type_dist.to_dict(orient="records"),
    }
