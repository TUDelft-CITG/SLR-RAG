from pathlib import Path
import pandas as pd
from pandera import String, Int64
import pandera.pandas as pa
from datetime import datetime
from typing import Optional
from pandera.typing import Series
# --- User-defined variables ---
AUTOMATICALLY_OVERWRITE = False

PROJECT_ROOT = Path(__file__).parent.parent.parent
PATH_INPUT = PROJECT_ROOT / Path("data/export_databases/")
PATH_LENS_EXPORT = PATH_INPUT / "lens-export.csv"
PATH_DIMENSIONS_EXPORT = PATH_INPUT / "dimensions-export.csv"

OUTPUT_PATH = PATH_INPUT  # Convenient when backuping the results
OUTPUT_CSV_AGENTS_PATH = OUTPUT_PATH / "paper_analysis.csv"
OUTPUT_CSV_QUERY_RESULTS = OUTPUT_PATH / "papers_selected.csv"
OUTPUT_UPSET = OUTPUT_PATH / "upset.html"
OUTPUT_CSV_SCOPUS = OUTPUT_PATH / "scopus_results.csv"
OUTPUT_CSV_OPENALEX = OUTPUT_PATH / "openalex_results.csv"

SCOPUS_IS_SUBSCRIBER = True
THRESHOLD_BIG_COUNT_PAPER = 1
DEFAULT_OPEN_ALEX_PAGING = 50

# Globl variables column names in dataframes

NAME_COL_DOI = "doi"
NAME_COL_TITLE = "title"
NAME_COL_DATE = "date"
NAME_COL_ABSTRACT = "abstract"
NAME_COL_TYPE = "type"
NAME_COL_PDF = "pdf"
NAME_COL_IS_REFERENCE = "is_reference"

NAME_COL_IS_FOUND = "is_found"
NAME_COL_YEAR = "year"
NAME_COL_ID_SCOPUS = "id_scopus"
NAME_COL_ID_OPENALEX = "id_openalex"
NAME_COL_ID_LENS = "id_lens"
NAME_COL_ID_DIMENSIONS = "id_dimensions"
NAME_COL_IN_SCOPUS = "in_scopus"
NAME_COL_IN_OPENALEX = "in_openalex"
NAME_COL_IN_LENS = "in_lens"
NAME_COL_IN_DIMENSIONS = "in_dimensions"
NAME_COL_PRESENT_SCOPUS = "present_scopus"
NAME_COL_PRESENT_OPENALEX = "present_openalex"
NAME_COL_PRESENT_LENS = "present_lens"
NAME_COL_PRESENT_DIMENSIONS = "present_dimensions"
NAME_COL_TOPIC_OPENALEX = "topic_openalex"
NAME_COL_TOPIC_LENS = "topic_lens"
NAME_COL_TOPIC_DIMENSION = "topic_dimensions"

# Type categories

NAME_DOCUMENT_TYPE_ARTICLE = "article"
NAME_DOCUMENT_TYPE_BOOK_CHAPTER = "book-chapter"
NAME_DOCUMENT_TYPE_DISSERTATION = "dissertation"
NAME_DOCUMENT_TYPE_CONFERENCE_PAPER = "conference-paper"
NAME_DOCUMENT_TYPE_CONFERENCE_PROCEEDING = "conference-proceeding"
NAME_DOCUMENT_TYPE_SEMINAR = "seminar"
NAME_DOCUMENT_TYPE_PREPRINT = "preprint"
NAME_DOCUMENT_TYPE_BOOK = "book"
NAME_DOCUMENT_TYPE_REPORT = "report"
NAME_DOCUMENT_TYPE_SOFTWARE = "software"
NAME_DOCUMENT_TYPE_OTHER = "other"


ALL_ARTICLE_TYPES = [
    NAME_DOCUMENT_TYPE_ARTICLE,
    NAME_DOCUMENT_TYPE_BOOK_CHAPTER,
    NAME_DOCUMENT_TYPE_DISSERTATION,
    NAME_DOCUMENT_TYPE_CONFERENCE_PAPER,
    NAME_DOCUMENT_TYPE_PREPRINT,
    NAME_DOCUMENT_TYPE_BOOK,
    NAME_DOCUMENT_TYPE_REPORT,
    NAME_DOCUMENT_TYPE_OTHER,
    NAME_DOCUMENT_TYPE_CONFERENCE_PROCEEDING,
    NAME_DOCUMENT_TYPE_SEMINAR,
    NAME_DOCUMENT_TYPE_SOFTWARE,
    None,
    pd.NA
]
# Mapping from possible input values to canonical categories


ARTICLE_TYPE_MAPPING = {
    # NAME_DOCUMENT_TYPE_ARTICLE
    "article": NAME_DOCUMENT_TYPE_ARTICLE,
    "journal article": NAME_DOCUMENT_TYPE_ARTICLE,
    "short survey": NAME_DOCUMENT_TYPE_ARTICLE,
    "review": NAME_DOCUMENT_TYPE_ARTICLE,
    # NAME_DOCUMENT_TYPE_BOOK_CHAPTER
    "book chapter": NAME_DOCUMENT_TYPE_BOOK_CHAPTER,
    "chapter": NAME_DOCUMENT_TYPE_BOOK_CHAPTER,
    "book-chapter": NAME_DOCUMENT_TYPE_BOOK_CHAPTER,
    # NAME_DOCUMENT_TYPE_PREPRINT
    "preprint": NAME_DOCUMENT_TYPE_PREPRINT,
    # NAME_DOCUMENT_TYPE_BOOK
    "book": NAME_DOCUMENT_TYPE_BOOK,
    "edited book": NAME_DOCUMENT_TYPE_BOOK,
    "monograph": NAME_DOCUMENT_TYPE_BOOK,
    # NAME_DOCUMENT_TYPE_REPORT
    "report": NAME_DOCUMENT_TYPE_REPORT,
    # NAME_ARTICLE_CONFERENCE_PAPER
    "conference paper": NAME_DOCUMENT_TYPE_CONFERENCE_PAPER,
    # NAME_ARTICLE_CONFERENCE_PROCEEDING
    "proceeding": NAME_DOCUMENT_TYPE_CONFERENCE_PROCEEDING,
    "conference proceedings": NAME_DOCUMENT_TYPE_CONFERENCE_PROCEEDING,
    "conference proceedings article": NAME_DOCUMENT_TYPE_CONFERENCE_PROCEEDING,
    # NAME_DOCUMENT_TYPE_DISSERTATION
    "dissertation": NAME_DOCUMENT_TYPE_DISSERTATION,
    # NAME_ARTICLE_SEMINAR
    "seminar": NAME_DOCUMENT_TYPE_SEMINAR,
    # NAME_DOCUMENT_TYPE_SOFTWARE
    "software": NAME_DOCUMENT_TYPE_SOFTWARE,
    # Other
    "other": NAME_DOCUMENT_TYPE_OTHER,
    "conference review": NAME_DOCUMENT_TYPE_OTHER,
    "news": NAME_DOCUMENT_TYPE_OTHER,
    "dataset": NAME_DOCUMENT_TYPE_OTHER,
    "letter": NAME_DOCUMENT_TYPE_OTHER,
    "editorial": NAME_DOCUMENT_TYPE_OTHER,
    "journal volume": NAME_DOCUMENT_TYPE_OTHER,
    "component": NAME_DOCUMENT_TYPE_OTHER,
    "journal": NAME_DOCUMENT_TYPE_OTHER,
    "clinical trial": NAME_DOCUMENT_TYPE_OTHER,
    "journal issue": NAME_DOCUMENT_TYPE_OTHER,
    "erratum": NAME_DOCUMENT_TYPE_OTHER,
    "note": NAME_DOCUMENT_TYPE_OTHER,
    "retracted": NAME_DOCUMENT_TYPE_OTHER,
    "paratext": NAME_DOCUMENT_TYPE_OTHER,
    "peer-review": NAME_DOCUMENT_TYPE_OTHER,
}


class SchemaPapers(pa.DataFrameModel):
    """Pandera schema for the papers DataFrame.

    This schema defines the structure and data types for the papers DataFrame used
    throughout the SLR-RAG application. It includes core paper metadata fields
    (DOI, title, date, abstract, etc.) and database-specific fields to track which
    databases each paper was found in.

    The schema validates that:
    - Core fields like DOI, title, date, and abstract have the correct data types
    - Database ID fields (id_scopus, id_openalex, etc.) are optional strings
    - Boolean flags track reference status and database presence
    - Paper types are validated against known article types
    - Date fields are properly formatted as datetime objects

    Attributes:
        doi: Digital Object Identifier (primary identifier)
        title: Paper title
        type: Publication type (e.g., 'article', 'review', 'conference')
        year: Publication year
        date: Publication date
        abstract: Paper abstract text
        is_reference: Whether this paper is in the reference list
        is_found: Whether this paper was found in any database
        id_scopus, id_openalex, id_lens, id_dimensions: Database-specific IDs
        in_scopus, in_openalex, in_lens, in_dimensions: Flags indicating presence in each database
        present_scopus, present_openalex, present_lens, present_dimensions: Flags indicating if reference papers are in each database
        topic_openalex: Topics/categories from OpenAlex
    """

    doi: Series[str] = pa.Field(nullable=True, alias=NAME_COL_DOI)
    title: Series[String] = pa.Field(nullable=True, alias=NAME_COL_TITLE)

    type: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_TYPE, isin=ALL_ARTICLE_TYPES
    )
    year: Series[Int64] = pa.Field(nullable=True, alias=NAME_COL_YEAR, coerce=True)
    date: Series[datetime] = pa.Field(nullable=True, alias=NAME_COL_DATE)
    abstract: Series[String] = pa.Field(nullable=True, alias=NAME_COL_ABSTRACT)
    is_reference: Series[bool] = pa.Field(nullable=True, alias=NAME_COL_IS_REFERENCE)
    is_found: Series[bool] = pa.Field(nullable=True, alias=NAME_COL_IS_FOUND)

    # ID in databases
    id_scopus: Optional[Series[String]] = pa.Field(
        nullable=True, alias=NAME_COL_ID_SCOPUS
    )
    id_openalex: Optional[Series[String]] = pa.Field(
        nullable=True, alias=NAME_COL_ID_DIMENSIONS
    )
    id_lens: Optional[Series[String]] = pa.Field(nullable=True, alias=NAME_COL_ID_LENS)
    id_dimensions: Optional[Series[String]] = pa.Field(
        nullable=True, alias=NAME_COL_ID_DIMENSIONS
    )
    # If the paper is returned by the query
    in_scopus: Optional[Series[bool]] = pa.Field(
        nullable=True, alias=NAME_COL_IN_SCOPUS
    )
    in_openalex: Optional[Series[bool]] = pa.Field(
        nullable=True, alias=NAME_COL_IN_OPENALEX
    )
    in_lens: Optional[Series[bool]] = pa.Field(nullable=True, alias=NAME_COL_IN_LENS)
    in_dimensions: Optional[Series[bool]] = pa.Field(
        nullable=True, alias=NAME_COL_IN_DIMENSIONS
    )
    # If a paper has the reference paper in the database.
    present_scopus: Optional[Series[bool]] = pa.Field(
        nullable=True, alias=NAME_COL_PRESENT_SCOPUS
    )
    present_openalex: Optional[Series[bool]] = pa.Field(
        nullable=True, alias=NAME_COL_PRESENT_OPENALEX
    )
    present_lens: Optional[Series[bool]] = pa.Field(
        nullable=True, alias=NAME_COL_PRESENT_LENS
    )
    present_dimensions: Optional[Series[bool]] = pa.Field(
        nullable=True, alias=NAME_COL_PRESENT_DIMENSIONS
    )

    # Topic fields
    topic_openalex: Optional[Series[String]] = pa.Field(
        nullable=True, alias=NAME_COL_TOPIC_OPENALEX
    )

    @pa.parser("type")  #
    def _parse_type(cls, series: Series) -> Series:
        result = series.copy()
        non_null_mask = series.notna()

        if non_null_mask.any():
            processed = series[non_null_mask].astype(str).str.lower().str.strip()
            processed = processed.replace(ARTICLE_TYPE_MAPPING)
            result.loc[non_null_mask] = processed

        return result

    @pa.parser("date")
    def _convert_string_to_datetime(cls, series: Series) -> Series:
        """Convert string dates to datetime objects, preserving nulls."""
        return pd.to_datetime(series, errors="coerce")

    @pa.parser("year")
    def _convert_year_to_int(cls, series: Series) -> Series:
        """Convert float year values to integers, preserving nulls."""
        if series.dtype == "float":
            return series.round().astype("Int64")
        return series

    class Config:
        add_missing_columns = True

PANDERA_LAZY_VALIDATION = True
DEFAULT_DF_COLUMNS = [
    NAME_COL_DOI,
    NAME_COL_TITLE,
    NAME_COL_DATE,
    NAME_COL_ABSTRACT,
    NAME_COL_TYPE,
]
DEFAULT_DF_COLUMNS_LENS = DEFAULT_DF_COLUMNS + ["id_lens", NAME_COL_TOPIC_LENS]
DEFAULT_DF_COLUMNS_DIMENSIONS = DEFAULT_DF_COLUMNS + [
    "id_dimensions",
    NAME_COL_TOPIC_DIMENSION,
]
