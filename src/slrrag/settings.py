from pathlib import Path
import pandera.pandas as pa
from datetime import datetime
from typing import Optional
from pandera.typing import Series, Int64
from slrrag.input import REFERENCE_PAPERS

# --- User-defined variables ---
REFERENCE_DOIS = [paper[1] for paper in REFERENCE_PAPERS]

AUTOMATICALLY_OVERWRITE = False

PROJECT_ROOT = Path(__file__).parent.parent.parent
PATH_INPUT = PROJECT_ROOT / Path("data/export_databases/")
PATH_LENS_EXPORT = PATH_INPUT / "lens-export.csv"
PATH_DIMENSIONS_EXPORT = PATH_INPUT / "dimensions-export.csv"

OUTPUT_PATH = PATH_INPUT  # Convenient when backuping the results
OUTPUT_CSV_AGENTS_PATH = OUTPUT_PATH / "paper_analysis.csv"
OUTPUT_CSV_QUERY_RESULTS = OUTPUT_PATH / "papers_selected.csv"
OUTPUT_UPSET = OUTPUT_PATH / "upset.html"


SCOPUS_IS_SUBSCRIBER = True
THRESHOLD_BIG_COUNT_PAPER = 1
DEFAULT_OPEN_ALEX_PAGING = 50

LIST_NAME_DATABASE = ["scopus", "openalex"]

NAME_ARTICLE_TYPE_ARTICLE = "article"
NAME_ARTICLE_TYPE_BOOK_CHAPTER = "book-chapter"
NAME_ARTICLE_TYPE_DISSERTATION = "dissertation"
NAME_ARTICLE_TYPE_PREPRINT = "preprint"
NAME_ARTICLE_TYPE_BOOK = "book"
NAME_ARTICLE_TYPE_REPORT = "report"
NAME_ARTICLE_TYPE_OTHER = "other"

LIST_TYPE_DOCUMENTS = [
    NAME_ARTICLE_TYPE_ARTICLE,
    NAME_ARTICLE_TYPE_BOOK_CHAPTER,
    NAME_ARTICLE_TYPE_DISSERTATION,
    NAME_ARTICLE_TYPE_PREPRINT,
    NAME_ARTICLE_TYPE_BOOK,
    NAME_ARTICLE_TYPE_REPORT,
]

CONVERSION_DICT_ARTICLE_TYPE_OPENALEX = {
    "article": NAME_ARTICLE_TYPE_ARTICLE,
    "other": NAME_ARTICLE_TYPE_OTHER,
    "book-chapter": NAME_ARTICLE_TYPE_BOOK_CHAPTER,
    "book": NAME_ARTICLE_TYPE_BOOK,
    "report": NAME_ARTICLE_TYPE_REPORT,
    "dissertation": NAME_ARTICLE_TYPE_DISSERTATION,
    "preprint": NAME_ARTICLE_TYPE_PREPRINT,
}

CONVERSION_DICT_LENS = {
    "book chapter": NAME_ARTICLE_TYPE_BOOK_CHAPTER,
    "journal article": NAME_ARTICLE_TYPE_ARTICLE,
    "preprint": NAME_ARTICLE_TYPE_PREPRINT,
    "book": NAME_ARTICLE_TYPE_BOOK,
    "dissertation": NAME_ARTICLE_TYPE_DISSERTATION,
    "report": NAME_ARTICLE_TYPE_REPORT,
}


NAME_COL_DOI = "doi"
NAME_COL_TITLE = "title"
NAME_COL_DATE = "date"
NAME_COL_ABSTRACT = "abstract"
NAME_COL_TYPE = "type"
NAME_COL_PDF = "pdf"
NAME_COL_IS_REFERENCE = "is_reference"

# New global variables for missing columns
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


class SchemaPapers(pa.DataFrameModel):
    doi: Series[str] = pa.Field(nullable=True, alias=NAME_COL_DOI)
    title: Series[str] = pa.Field(nullable=True, alias=NAME_COL_TITLE)
    date: Series[datetime] = pa.Field(nullable=True, alias=NAME_COL_DATE)
    abstract: Series[str] = pa.Field(nullable=True, alias=NAME_COL_ABSTRACT)
    is_reference: Series[bool] = pa.Field(nullable=True, alias=NAME_COL_IS_REFERENCE)
    is_found: Series[bool] = pa.Field(nullable=True, alias=NAME_COL_IS_FOUND)
    year: Series[Int64] = pa.Field(nullable=True, alias=NAME_COL_YEAR)

    # Optional fields
    id_scopus: Optional[Series[str]] = pa.Field(nullable=True, alias=NAME_COL_ID_SCOPUS)
    id_openalex: Optional[Series[str]] = pa.Field(
        nullable=True, alias=NAME_COL_ID_OPENALEX
    )
    id_lens: Optional[Series[str]] = pa.Field(nullable=True, alias=NAME_COL_ID_LENS)
    id_dimensions: Optional[Series[str]] = pa.Field(
        nullable=True, alias=NAME_COL_ID_DIMENSIONS
    )
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


DEFAULT_DF_COLUMNS = [
    NAME_COL_DOI,
    NAME_COL_TITLE,
    NAME_COL_DATE,
    NAME_COL_ABSTRACT,
    NAME_COL_TYPE,
]
DEFAULT_DF_COLUMNS_LENS = DEFAULT_DF_COLUMNS + ["id_lens"]
DEFAULT_DF_COLUMNS_DIMENSIONS = DEFAULT_DF_COLUMNS + ["id_dimensions"]
