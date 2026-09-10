from datetime import datetime
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera import Int64, String
from pandera.typing import Series

# --- User-defined variables ---
AUTOMATICALLY_OVERWRITE = True

PROJECT_ROOT = Path(__file__).parent.parent.parent
PATH_DATA = PROJECT_ROOT / Path("data/papers_selection/")
PATH_INPUT = PATH_DATA
PATH_LENS_EXPORT = PATH_DATA / "lens-export.csv"
PATH_DIMENSIONS_EXPORT = PATH_DATA / "dimensions-export.csv"


# --- Outputs variables ---

PATH_OUTPUT = PATH_DATA  # Convenient when backuping the results

# Output of all papers without filtering
PATH_CSV_01_QUERY_RESULTS = PATH_OUTPUT / "01_papers_query_results.csv"
PATH_CSV_SCOPUS_QUERY_RESULTS = PATH_OUTPUT / "scopus_query_results.csv"
PATH_CSV_OPENALEX_QUERY_RESULTS = PATH_OUTPUT / "openalex_query_results.csv"

# Output of papers with manual filter (topic, date, type...)
PATH_CSV_02_FILTERED_TOPIC = PATH_OUTPUT / "02_papers_filtered_topic.csv"

# Outputs of papers with first_round_question answerd by the agents.
PATH_CSV_03_AGENTS_ANWSERS = PATH_OUTPUT / "03_papers_agent_anwsers_v3.csv"

# Outputs of papers with manual_filters
PATH_CSV_04_MANUAL_FILTER = PATH_OUTPUT / "04_papers_manual_filter.csv"

# Outputs of 111 papers picked
PATH_CSV_06 = PATH_OUTPUT / "06_picky_selection.csv"


# Output of upset plot
PATH_UPSET_DISTINCT = PATH_OUTPUT / "upset_distinct.html"
PATH_UPSET_INTERSECT = PATH_OUTPUT / "upset_intersect.html"

# Path of config for pybliometrics

PATH_PYBLIOMETRICS_CONFIG = PROJECT_ROOT / "pybliometrics.cfg"

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
NAME_COL_PRIMARY_TOPIC_OPENALEX = "topic_openalex"
NAME_COL_PRIMARY_FIELD_OPENALEX = "fields_openalex"
NAME_COL_PRIMARY_SUBFIELD_OPENALEX = "subfields_openalex"
NAME_COL_PRIMARY_DOMAIN_OPENALEX = "domain_openalex"

NAME_COL_TOPIC_LENS = "topic_lens"
NAME_COL_TOPIC_DIMENSIONS = "topic_dimensions"
NAME_COL_KEYWORDS_SCOPUS = "keywords_scopus"
NAME_COL_KEYWORDS_OPENALEX = "keywords_openalex"
NAME_COL_RELEVANCE_OPENALEX = "relevance_openalex"
NAME_COL_RELEVANCE_ORDER_SCOPUS = "relevance_order_scopus"

NAME_COL_KEYWORDS_LENS = "keywords_lens"

NAME_COL_KEYWORDS_DIMENSIONS = "keywords_dimensions"

# Type categories

ARTICLE_N = "article"
BOOK_CHAPTER_N = "book-chapter"
DISSERTATION_N = "dissertation"
CONFERENCE_PAPER_N = "conference-paper"
CONFERENCE_PROCEEDING_N = "conference-proceeding"
SEMINAR_N = "seminar"
PREPRINT_N = "preprint"
BOOK_N = "book"
REPORT_N = "report"
SOFTWARE_N = "software"
OTHER_N = "other"


ALL_ARTICLE_TYPES = [
    ARTICLE_N,
    BOOK_CHAPTER_N,
    DISSERTATION_N,
    CONFERENCE_PAPER_N,
    CONFERENCE_PROCEEDING_N,
    SEMINAR_N,
    PREPRINT_N,
    BOOK_N,
    REPORT_N,
    SOFTWARE_N,
    OTHER_N,
    None,
    pd.NA,
]
# Mapping from possible input values to canonical categories


ARTICLE_TYPE_MAPPING = {
    # NAME_DOCUMENT_TYPE_ARTICLE
    "article": ARTICLE_N,
    "journal article": ARTICLE_N,
    "short survey": ARTICLE_N,
    "review": ARTICLE_N,
    # NAME_DOCUMENT_TYPE_BOOK_CHAPTER
    "book chapter": BOOK_CHAPTER_N,
    "chapter": BOOK_CHAPTER_N,
    "book-chapter": BOOK_CHAPTER_N,
    # NAME_DOCUMENT_TYPE_PREPRINT
    "preprint": PREPRINT_N,
    # NAME_DOCUMENT_TYPE_BOOK
    "book": BOOK_N,
    "edited book": BOOK_N,
    "monograph": BOOK_N,
    # NAME_DOCUMENT_TYPE_REPORT
    "report": REPORT_N,
    # NAME_ARTICLE_CONFERENCE_PAPER
    "conference paper": CONFERENCE_PAPER_N,
    # NAME_ARTICLE_CONFERENCE_PROCEEDING
    "proceeding": CONFERENCE_PROCEEDING_N,
    "conference proceedings": CONFERENCE_PROCEEDING_N,
    "conference proceedings article": CONFERENCE_PROCEEDING_N,
    # NAME_DOCUMENT_TYPE_DISSERTATION
    "dissertation": DISSERTATION_N,
    # NAME_ARTICLE_SEMINAR
    "seminar": SEMINAR_N,
    # NAME_DOCUMENT_TYPE_SOFTWARE
    "software": SOFTWARE_N,
    # Other
    "other": OTHER_N,
    "conference review": OTHER_N,
    "news": OTHER_N,
    "dataset": OTHER_N,
    "letter": OTHER_N,
    "editorial": OTHER_N,
    "journal volume": OTHER_N,
    "component": OTHER_N,
    "journal": OTHER_N,
    "clinical trial": OTHER_N,
    "journal issue": OTHER_N,
    "erratum": OTHER_N,
    "note": OTHER_N,
    "retracted": OTHER_N,
    "paratext": OTHER_N,
    "peer-review": OTHER_N,
    "conference-abstract": OTHER_N,
    "reference-entry": OTHER_N,
    "book-review": OTHER_N,
}


#  -----Pandera specifications-----
PANDERA_LAZY_VALIDATION = True


class SchemaPapers(pa.DataFrameModel):
    """Pandera schema for the papers DataFrame.

    This schema defines the structure and data types for the papers DataFrame used
    throughout the SLR-RAG application. It includes core paper metadata fields
    (DOI, title, date, abstract, etc.).

    The schema validates that:
    - Core fields like DOI, title, date, and abstract have the correct data types
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
    """

    doi: Series[str] = pa.Field(nullable=True, alias=NAME_COL_DOI)
    title: Series[String] = pa.Field(nullable=True, alias=NAME_COL_TITLE)

    type: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_TYPE, isin=ALL_ARTICLE_TYPES
    )
    year: Series[Int64] = pa.Field(nullable=True, alias=NAME_COL_YEAR, coerce=True)
    date: Series[datetime] = pa.Field(nullable=True, alias=NAME_COL_DATE)
    abstract: Series[String] = pa.Field(nullable=True, alias=NAME_COL_ABSTRACT)

    @pa.parser("type")
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


class SchemaScopusPapers(SchemaPapers):
    # ID in databases (a link if possible)

    id_scopus: Series[String] = pa.Field(nullable=True, alias=NAME_COL_ID_SCOPUS)

    keywords_scopus: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_KEYWORDS_SCOPUS, coerce=True
    )
    # Order of the paper after being sort by relevance
    relevance_order_scopus: Series[Int64] = pa.Field(
        nullable=True, alias=NAME_COL_RELEVANCE_ORDER_SCOPUS, coerce=True
    )


class SchemaOpenAlexPapers(SchemaPapers):
    # ID in databases (a link if possible)

    id_openalex: Series[String] = pa.Field(nullable=True, alias=NAME_COL_ID_OPENALEX)

    # Topic fields : https://developers.openalex.org/api-reference/topics
    topic_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_PRIMARY_TOPIC_OPENALEX, coerce=True
    )

    # Field fields : https://developers.openalex.org/api-reference/fields
    fields_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_PRIMARY_FIELD_OPENALEX, coerce=True
    )
    subfields_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_PRIMARY_SUBFIELD_OPENALEX, coerce=True
    )
    domain_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_PRIMARY_DOMAIN_OPENALEX, coerce=True
    )
    pdf: Series[String] = pa.Field(nullable=True, alias=NAME_COL_PDF, coerce=True)

    keywords_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_KEYWORDS_OPENALEX, coerce=True
    )
    relevance_openale: Series[float] = pa.Field(
        nullable=True, alias=NAME_COL_RELEVANCE_OPENALEX, coerce=True
    )


class SchemaLensPapers(SchemaPapers):
    # ID in databases (a link if possible)

    id_lens: Series[String] = pa.Field(nullable=True, alias=NAME_COL_ID_LENS)

    # Topic fields
    topic_lens: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_TOPIC_LENS, coerce=True
    )
    keywords_lens: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_KEYWORDS_LENS, coerce=True
    )


class SchemaDimensionsPapers(SchemaPapers):
    # ID in databases (a link if possible)

    id_dimensions: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_ID_DIMENSIONS
    )
    # Topic fields
    topic_dimensions: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_TOPIC_DIMENSIONS, coerce=True
    )

    keywords_dimensions: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_KEYWORDS_DIMENSIONS, coerce=True
    )


class SchemaAnalysisPapers(SchemaPapers):
    is_reference: Series[bool] = pa.Field(nullable=True, alias=NAME_COL_IS_REFERENCE)

    # Fields to know if a reference paper has been found
    is_found: Series[bool] = pa.Field(nullable=True, alias=NAME_COL_IS_FOUND)


DEFAULT_DF_COLUMNS = [
    NAME_COL_DOI,
    NAME_COL_TITLE,
    NAME_COL_DATE,
    NAME_COL_ABSTRACT,
    NAME_COL_TYPE,
]
SCOPUS_IS_SUBSCRIBER = True
THRESHOLD_BIG_COUNT_PAPER = 1
DEFAULT_OPEN_ALEX_PAGING = 50
