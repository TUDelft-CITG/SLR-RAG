# --- Dimensions functions ---
from pathlib import Path

import pandas as pd

from slrrag.settings import (
    DEFAULT_DF_COLUMNS_DIMENSIONS,
    NAME_ARTICLE_TYPE_ARTICLE,
    NAME_ARTICLE_TYPE_BOOK,
    NAME_ARTICLE_TYPE_BOOK_CHAPTER,
    NAME_ARTICLE_TYPE_PREPRINT,
    NAME_COL_ABSTRACT,
    NAME_COL_DATE,
    NAME_COL_DOI,
    NAME_COL_TITLE,
    NAME_COL_TYPE,
)


def read_dimensions_export(csv_path: Path | str) -> pd.DataFrame:
    """Read Dimensions export CSV and extract required columns: title, doi, abstract, date, id_dimensions."""
    df = pd.read_csv(csv_path, skiprows=1)
    # Map Dimensions column names to our standard format
    column_mapping = {
        "Title": NAME_COL_TITLE,
        "DOI": NAME_COL_DOI,
        "Abstract": NAME_COL_ABSTRACT,
        "Publication date": NAME_COL_DATE,
        "Publication type": NAME_COL_TYPE,
        "Dimensions URL": "id_dimensions",
    }
    # Rename columns that exist
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    # Select only the columns we need, filling missing ones with None
    result_cols = DEFAULT_DF_COLUMNS_DIMENSIONS
    for col in result_cols:
        if col not in df.columns:
            df[col] = None

    conversion_type_article_dimensions = {
        "Article": NAME_ARTICLE_TYPE_ARTICLE,
        "Chapter": NAME_ARTICLE_TYPE_BOOK_CHAPTER,
        "Edited Book": NAME_ARTICLE_TYPE_BOOK,
        "Preprint": NAME_ARTICLE_TYPE_PREPRINT,
        "Monograph": NAME_ARTICLE_TYPE_BOOK,
    }
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    df = df.replace({NAME_COL_TYPE: conversion_type_article_dimensions})
    return df[result_cols].copy()
