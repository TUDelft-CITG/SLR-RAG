
# --- Lens functions ---
from pathlib import Path

import pandas as pd

from settings import DEFAULT_DF_COLUMNS_LENS


def read_lens_export(csv_path: Path | str) -> pd.DataFrame:
    """Read Lens export CSV and extract required columns: doi, id, title, date, abstract."""
    df = pd.read_csv(csv_path)
    # Map common Lens column names to our standard format
    column_mapping = {
        "Title": "title",
        "DOI": "doi",
        "Abstract": "abstract",
        "Publication Year": "date",
        "Lens ID": "id_lens",
    }
    # Rename columns that exist
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    # Select only the columns we need, filling missing ones with None
    result_cols = DEFAULT_DF_COLUMNS_LENS
    for col in result_cols:
        if col not in df.columns:
            df[col] = None
    df["date"] = pd.to_datetime(df["date"],format="mixed")
    return df[result_cols].copy()
