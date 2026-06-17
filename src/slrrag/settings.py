from pathlib import Path
import pandas as pd
from pandera import String, Int64
import pandera.pandas as pa
from datetime import datetime
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
PATH_CSV_03_AGENTS_ANWSERS = PATH_OUTPUT / "03_papers_agent_anwsers.csv"

# Outputs of papers with manual_filters
PATH_CSV_04_MANUAL_FILTER = PATH_OUTPUT / "04_papers_manual_filter.csv"

# Output of upset plot
PATH_UPSET = PATH_OUTPUT / "upset.html"




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
    pd.NA,
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


class SchemaScopusPapers(SchemaPapers):
    # ID in databases (a link if possible)

    id_scopus: Series[String] = pa.Field(nullable=True, alias=NAME_COL_ID_SCOPUS)

    keywords_scopus: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_KEYWORDS_SCOPUS
    )
    # Order of the paper after being sort by relevance
    relevance_order_scopus: Series[Int64] = pa.Field(
        nullable=True, alias=NAME_COL_RELEVANCE_ORDER_SCOPUS
    )


class SchemaOpenAlexPapers(SchemaPapers):
    # ID in databases (a link if possible)

    id_openalex: Series[String] = pa.Field(nullable=True, alias=NAME_COL_ID_OPENALEX)

    # Topic fields : https://developers.openalex.org/api-reference/topics
    topic_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_PRIMARY_TOPIC_OPENALEX
    )

    # Field fields : https://developers.openalex.org/api-reference/fields
    fields_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_PRIMARY_FIELD_OPENALEX
    )
    subfields_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_PRIMARY_SUBFIELD_OPENALEX
    )
    domain_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_PRIMARY_DOMAIN_OPENALEX
    )
    pdf: Series[String] = pa.Field(nullable=True, alias=NAME_COL_PDF)

    keywords_openalex: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_KEYWORDS_OPENALEX
    )
    relevance_openale: Series[float] = pa.Field(
        nullable=True, alias=NAME_COL_RELEVANCE_OPENALEX
    )


class SchemaLensPapers(SchemaPapers):
    # ID in databases (a link if possible)

    id_lens: Series[String] = pa.Field(nullable=True, alias=NAME_COL_ID_LENS)

    # Topic fields
    topic_lens: Series[String] = pa.Field(nullable=True, alias=NAME_COL_TOPIC_LENS)
    keywords_lens: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_KEYWORDS_LENS
    )


class SchemaDimensionsPapers(SchemaPapers):
    # ID in databases (a link if possible)

    id_dimensions: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_ID_DIMENSIONS
    )
    # Topic fields
    topic_dimensions: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_TOPIC_DIMENSIONS
    )

    keywords_dimensions: Series[String] = pa.Field(
        nullable=True, alias=NAME_COL_KEYWORDS_DIMENSIONS
    )


class SchemaAnalysisPapers(SchemaPapers):
    is_reference: Series[bool] = pa.Field(nullable=True, alias=NAME_COL_IS_REFERENCE)

    # Fields to know if a reference paper has been found
    is_found: Series[bool] = pa.Field(nullable=True, alias=NAME_COL_IS_FOUND)


PANDERA_LAZY_VALIDATION = False
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