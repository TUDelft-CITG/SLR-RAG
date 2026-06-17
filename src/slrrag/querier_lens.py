# --- Lens functions ---
from pathlib import Path

import pandas as pd
from pandera.typing import DataFrame
from slrrag.settings import (
    DEFAULT_DF_COLUMNS,
    NAME_COL_KEYWORDS_LENS,
    ARTICLE_N,
    BOOK_N,
    BOOK_CHAPTER_N,
    DISSERTATION_N,
    PREPRINT_N,
    REPORT_N,
    NAME_COL_ABSTRACT,
    NAME_COL_DATE,
    NAME_COL_DOI,
    NAME_COL_TITLE,
    NAME_COL_TOPIC_LENS,
    NAME_COL_TYPE,
    PANDERA_LAZY_VALIDATION,
    SchemaLensPapers,
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
        "Keywords": NAME_COL_KEYWORDS_LENS,
    }

    # Rename columns that exist
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
    # Convert the ; that lens use to seprate topics in list, that can be explodable later.

    # Select only the columns we need, filling missing ones with None
    columns_to_keep = DEFAULT_DF_COLUMNS + [
        "id_lens",
        NAME_COL_TOPIC_LENS,
        NAME_COL_KEYWORDS_LENS,
    ]
    for col in columns_to_keep:
        if col not in df.columns:
            df[col] = None
    df["date"] = pd.to_datetime(df["date"], format="mixed")
    conversion_type_article_lens = {
        "book chapter": BOOK_CHAPTER_N,
        "journal article": ARTICLE_N,
        "preprint": PREPRINT_N,
        "book": BOOK_N,
        "dissertation": DISSERTATION_N,
        "report": REPORT_N,
    }
    df = df.replace({NAME_COL_TYPE: conversion_type_article_lens})
    return SchemaLensPapers.validate(
        df[columns_to_keep].copy(), lazy=PANDERA_LAZY_VALIDATION
    )
