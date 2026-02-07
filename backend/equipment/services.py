"""
CSV processing service using Pandas.
Handles parsing, validation, and bulk-creation of EquipmentData rows.
"""

import pandas as pd
from pandas.errors import EmptyDataError

from .models import EquipmentData, UploadHistory

REQUIRED_COLUMNS = {"equipment_name", "type", "flowrate", "pressure", "temperature"}
NUMERIC_PARAMS = ["flowrate", "pressure", "temperature"]


class CSVProcessingError(Exception):
    """Raised when the uploaded CSV cannot be processed."""
    pass


def process_csv(file, user):
    """
    Parse an uploaded CSV file and insert validated rows into the database.

    Expected CSV columns:
        equipment_name, type, flowrate, pressure, temperature

    Returns:
        dict with keys: rows_imported, equipment_count
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
            f"Expected: equipment_name, type, flowrate, pressure, temperature"
        )

    # Drop rows where equipment_name is NaN
    df = df.dropna(subset=["equipment_name"])

    if df.empty:
        raise CSVProcessingError("CSV contains no valid data rows after cleaning.")

    # Coerce numeric columns
    for col in NUMERIC_PARAMS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=NUMERIC_PARAMS)

    if df.empty:
        raise CSVProcessingError("No valid numeric values found in flowrate/pressure/temperature columns.")

    # Fill optional type column
    df["type"] = df["type"].fillna("")

    # Record upload history first so we can link rows to it
    upload = UploadHistory.objects.create(
        user=user,
        file_name=getattr(file, "name", "unknown.csv"),
        rows_imported=len(df),
    )

    # Bulk create with FK to upload
    objects = [
        EquipmentData(
            user=user,
            upload=upload,
            equipment_name=str(row["equipment_name"]).strip(),
            equipment_type=str(row["type"]).strip(),
            flowrate=row["flowrate"],
            pressure=row["pressure"],
            temperature=row["temperature"],
        )
        for _, row in df.iterrows()
    ]
    EquipmentData.objects.bulk_create(objects)

    # ── Keep only the 5 most recent uploads; delete older ones ──
    MAX_UPLOADS = 5
    recent_ids = list(
        UploadHistory.objects.filter(user=user)
        .order_by("-uploaded_at")
        .values_list("id", flat=True)[:MAX_UPLOADS]
    )
    if recent_ids:
        # Cascade-delete old uploads and their linked EquipmentData rows
        UploadHistory.objects.filter(user=user).exclude(id__in=recent_ids).delete()

    return {
        "rows_imported": len(objects),
        "equipment_count": df["equipment_name"].nunique(),
        "upload_id": upload.id,
    }


def get_summary_stats(user, upload_id=None):
    """
    Return aggregated statistics for a user's equipment data.
    If upload_id is given, restrict to that single upload's rows.

    Returns dict with:
        - total_records
        - equipment_list: [{name, type, avg_flowrate, avg_pressure, avg_temperature, count}]
        - parameter_averages: {flowrate, pressure, temperature} (overall averages)
    """
    qs = EquipmentData.objects.filter(user=user)
    if upload_id is not None:
        qs = qs.filter(upload_id=upload_id)

    if not qs.exists():
        return {"total_records": 0, "equipment_list": [], "parameter_averages": {}}

    df = pd.DataFrame(
        list(qs.values("equipment_name", "equipment_type", "flowrate", "pressure", "temperature"))
    )

    # Per-equipment aggregation
    equip_agg = df.groupby(["equipment_name", "equipment_type"]).agg(
        avg_flowrate=("flowrate", "mean"),
        avg_pressure=("pressure", "mean"),
        avg_temperature=("temperature", "mean"),
        count=("flowrate", "count"),
    ).reset_index()
    equip_agg = equip_agg.rename(columns={"equipment_name": "name", "equipment_type": "type"})
    for col in ["avg_flowrate", "avg_pressure", "avg_temperature"]:
        equip_agg[col] = equip_agg[col].round(2)

    # Overall parameter averages
    parameter_averages = {
        "flowrate": round(df["flowrate"].mean(), 2),
        "pressure": round(df["pressure"].mean(), 2),
        "temperature": round(df["temperature"].mean(), 2),
    }

    # Type distribution (count per equipment_type)
    type_dist = (
        df.groupby("equipment_type")
        .size()
        .reset_index(name="count")
        .rename(columns={"equipment_type": "type"})
        .sort_values("count", ascending=False)
    )

    return {
        "total_records": len(df),
        "equipment_list": equip_agg.to_dict(orient="records"),
        "parameter_averages": parameter_averages,
        "type_distribution": type_dist.to_dict(orient="records"),
    }
