# --- Lens functions ---
from pathlib import Path

import pandas as pd
from pandera.typing import DataFrame
from slrrag.settings import (
    DEFAULT_DF_COLUMNS_LENS,
    NAME_DOCUMENT_TYPE_ARTICLE,
    NAME_DOCUMENT_TYPE_BOOK,
    NAME_DOCUMENT_TYPE_BOOK_CHAPTER,
    NAME_DOCUMENT_TYPE_DISSERTATION,
    NAME_DOCUMENT_TYPE_PREPRINT,
    NAME_DOCUMENT_TYPE_REPORT,
    NAME_COL_ABSTRACT,
    NAME_COL_DATE,
    NAME_COL_DOI,
    NAME_COL_TITLE,
    NAME_COL_TOPIC_LENS,
    NAME_COL_TYPE,
    PANDERA_LAZY_VALIDATION,
    SchemaPapers,
)


def read_lens_export(csv_path: Path | str) -> DataFrame[SchemaPapers]:
    """Read Lens export CSV and extract required columns: doi, id, title, date, abstract."""
    df = pd.read_csv(csv_path)
    # Map common Lens column names to our standard format
    column_mapping = {
        "Title": NAME_COL_TITLE,
        "DOI": NAME_COL_DOI,
        "Abstract": NAME_COL_ABSTRACT,
        "Date Published": NAME_COL_DATE,
        "Publication Type": NAME_COL_TYPE,
        "Lens ID": "id_lens",
        "Fields of Study": NAME_COL_TOPIC_LENS,
    }

    # Rename columns that exist
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
    # Convert the ; that lens use to seprate topics in list, that can be explodable later.

    # Select only the columns we need, filling missing ones with None
    result_cols = DEFAULT_DF_COLUMNS_LENS
    for col in result_cols:
        if col not in df.columns:
            df[col] = None
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    conversion_type_article_lens = {
        "book chapter": NAME_DOCUMENT_TYPE_BOOK_CHAPTER,
        "journal article": NAME_DOCUMENT_TYPE_ARTICLE,
        "preprint": NAME_DOCUMENT_TYPE_PREPRINT,
        "book": NAME_DOCUMENT_TYPE_BOOK,
        "dissertation": NAME_DOCUMENT_TYPE_DISSERTATION,
        "report": NAME_DOCUMENT_TYPE_REPORT,
    }
    df = df.replace({NAME_COL_TYPE: conversion_type_article_lens})
    return SchemaPapers.validate(df[result_cols].copy(),lazy=PANDERA_LAZY_VALIDATION)
