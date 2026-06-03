# --- Dimensions functions ---
from pathlib import Path

import pandas as pd
from pandera.typing import DataFrame
import pandera.pandas as pa
from slrrag.settings import (
    DEFAULT_DF_COLUMNS_DIMENSIONS,
    NAME_COL_ABSTRACT,
    NAME_COL_DATE,
    NAME_COL_DOI,
    NAME_COL_TITLE,
    NAME_COL_TOPIC_DIMENSIONS,
    NAME_COL_TYPE,
    PANDERA_LAZY_VALIDATION,
    SchemaPapers,
)


@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def read_dimensions_export(csv_path: Path | str) -> DataFrame[SchemaPapers]:
    """Read Dimensions export CSV and extract required columns: title, doi, abstract, date, id_dimensions."""
    df = pd.read_csv(csv_path, skiprows=1)
    # Map Dimensions column names to our standard format
    column_mapping = {
        "Title": NAME_COL_TITLE,
        "DOI": NAME_COL_DOI,
        "Abstract": NAME_COL_ABSTRACT,
        "Publication date": NAME_COL_DATE,
        "Publication Type": NAME_COL_TYPE,
        "Dimensions URL": "id_dimensions",
        "Units of Assessment": NAME_COL_TOPIC_DIMENSIONS,
    }
    # Rename columns that exist
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
    return SchemaPapers.validate(df[DEFAULT_DF_COLUMNS_DIMENSIONS].copy(),lazy=PANDERA_LAZY_VALIDATION)
