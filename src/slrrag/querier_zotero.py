import os
import re

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm

from slrrag.settings import (
    NAME_COL_ABSTRACT,
    NAME_COL_AUTHORS_ZOTERO,
    NAME_COL_CONFERENCE_ZOTERO,
    NAME_COL_COUNTRY_ZOTERO,
    NAME_COL_DATE,
    NAME_COL_DOI,
    NAME_COL_JOURNAL_ZOTERO,
    NAME_COL_TITLE,
    NAME_COL_TYPE,
    NAME_COL_UNIVERSITY_ZOTERO,
    PATH_CSV_01_QUERY_RESULTS,
    PATH_CSV_ZOTERO_QUERY_RESULTS,
    PROJECT_ROOT,
)

# Zotero write API accepts at most 50 items per request
ZOTERO_MAX_ITEMS_PER_REQUEST = 50

# Mapping from our article types to Zotero item types
ZOTERO_ITEM_TYPE_MAPPING = {
    "article": "journalArticle",
    "conference-paper": "conferencePaper",
    "conference-proceeding": "conferencePaper",
    "preprint": "preprint",
    "book-chapter": "bookSection",
    "book": "book",
    "dissertation": "thesis",
    "report": "report",
    "seminar": "presentation",
    "software": "computerProgram",
    "other": "document",
}


def load_zotero_client():
    """Create a Zotero client from the credentials in PROJECT_ROOT/.env.

    Expected variables:
        ZOTERO_LIBRARY_ID=<numeric id>
        ZOTERO_API_KEY=<api key>
        ZOTERO_LIBRARY_TYPE=user   # or group
    """
    from pyzotero import zotero

    load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
    library_id = os.environ.get("ZOTERO_LIBRARY_ID")
    api_key = os.environ.get("ZOTERO_API_KEY")
    library_type = os.environ.get("ZOTERO_LIBRARY_TYPE", "user")

    if library_id is None or api_key is None:
        raise ValueError(
            f"ZOTERO_LIBRARY_ID or ZOTERO_API_KEY missing in {PROJECT_ROOT / '.env'}.\n"
            "Create an API key at https://www.zotero.org/settings/keys ."
        )
    return zotero.Zotero(library_id, library_type, api_key)


def get_collection_key(zot, name: str) -> str | None:
    """Return the key of the first collection whose name matches `name`."""
    for collection in zot.everything(zot.collections()):
        if collection["data"]["name"] == name:
            return collection["key"]
    return None


def create_collection(
    zot, collection_name: str, parent_collection_name: str | None = None
) -> str:
    """Create a collection (optionally nested inside a parent) and return its key."""
    parent_key = None
    if parent_collection_name is not None:
        parent_key = get_collection_key(zot, parent_collection_name)
        if parent_key is None:
            raise ValueError(f"Parent collection '{parent_collection_name}' not found.")

    resp = zot.create_collections(
        [{"name": collection_name, "parentCollection": parent_key}]
    )
    if resp.get("failed"):
        raise RuntimeError(f"Collection creation failed: {resp['failed']}")
    return resp["success"]["0"]


def paper_to_zotero_item(
    zot, paper: pd.Series, collection_key: str, templates_cache: dict
) -> dict:
    """Build a Zotero item dict from one row of the papers DataFrame."""
    item_type = ZOTERO_ITEM_TYPE_MAPPING.get(paper.get(NAME_COL_TYPE), "document")
    if item_type not in templates_cache:
        # Fetch the valid template for this type (fields not in it would be rejected)
        templates_cache[item_type] = zot.item_template(item_type)
    template = templates_cache[item_type].copy()

    template[NAME_COL_TITLE] = paper[NAME_COL_TITLE]
    template["collections"] = [collection_key]

    doi = paper.get(NAME_COL_DOI)
    if pd.notna(doi) and "DOI" in template:
        template["DOI"] = str(doi).removeprefix("https://doi.org/")

    abstract = paper.get(NAME_COL_ABSTRACT)
    if pd.notna(abstract) and "abstractNote" in template:
        template["abstractNote"] = str(abstract)

    date = paper.get(NAME_COL_DATE)
    if pd.notna(date) and "date" in template:
        template["date"] = str(pd.Timestamp(date).date())

    return template


def upload_papers_to_collection(zot, df_papers: pd.DataFrame, collection_key: str):
    """Upload every paper of the DataFrame into the collection, 50 at a time."""
    templates_cache = {}
    for start in tqdm(
        range(0, len(df_papers), ZOTERO_MAX_ITEMS_PER_REQUEST),
        total=1 + (len(df_papers) - 1) // ZOTERO_MAX_ITEMS_PER_REQUEST,
    ):
        batch = df_papers.iloc[start : start + ZOTERO_MAX_ITEMS_PER_REQUEST]
        items = [
            paper_to_zotero_item(zot, paper, collection_key, templates_cache)
            for _, paper in batch.iterrows()
        ]
        resp = zot.create_items(items)
        if resp.get("failed"):
            print(
                f"Warning: {len(resp['failed'])} item(s) rejected in batch: {resp['failed']}"
            )
        if not resp.get("success"):
            raise RuntimeError(f"Zotero rejected the batch: {resp}")


def parse_extra_field(item_data: dict, field: str) -> str | None:
    """Extract a 'Field: value' line from the Zotero Extra field."""
    extra = item_data.get("extra") or ""
    match = re.search(rf"{field}\s*:\s*(.+)", extra, flags=re.IGNORECASE)
    return match.group(1).strip() if match else None


def parse_country(item_data: dict) -> str | None:
    """Best-effort country extraction: 'Country:' in Extra, else last part of place."""
    country = parse_extra_field(item_data, "Country")
    if country:
        return country
    place = item_data.get("place")
    if place and "," in place:
        return place.split(",")[-1].strip()
    return None


def fetch_collection_metadata(zot, collection_key: str) -> pd.DataFrame:
    """Query Zotero for all items of the collection and extract the target fields."""
    records = []
    for item in zot.everything(zot.collection_items(collection_key)):
        data = item["data"]
        if data["itemType"] in ("attachment", "note"):
            continue

        authors = "; ".join(
            f"{c.get('lastName', '')}, {c.get('firstName', '')}".strip(", ")
            for c in data.get("creators", [])
            if c.get("creatorType") == "author"
        )
        records.append(
            {
                NAME_COL_DOI: data.get("DOI"),
                NAME_COL_TITLE: data.get("title"),
                NAME_COL_AUTHORS_ZOTERO: authors or None,
                NAME_COL_JOURNAL_ZOTERO: data.get("publicationTitle"),
                NAME_COL_CONFERENCE_ZOTERO: data.get("proceedingsTitle"),
                NAME_COL_UNIVERSITY_ZOTERO: data.get("university")
                or parse_extra_field(data, "University"),
                NAME_COL_COUNTRY_ZOTERO: parse_country(data),
            }
        )
    return pd.DataFrame(records)


def normalize_doi(doi) -> str | None:
    if pd.isna(doi):
        return None
    result = str(doi).removeprefix("https://doi.org/").strip().lower()
    return result or None


def update_dataframe_with_zotero(
    df_papers: pd.DataFrame, df_zotero: pd.DataFrame
) -> pd.DataFrame:
    """Merge the Zotero metadata back into the papers DataFrame.

    Papers are matched on normalized DOI first, then on title as a fallback
    (for papers without DOI).
    """
    df_merged = df_papers.copy()
    if df_zotero.empty:
        print("Warning: no Zotero metadata retrieved.")
        return df_merged

    zotero_columns = [
        NAME_COL_AUTHORS_ZOTERO,
        NAME_COL_JOURNAL_ZOTERO,
        NAME_COL_CONFERENCE_ZOTERO,
        NAME_COL_UNIVERSITY_ZOTERO,
        NAME_COL_COUNTRY_ZOTERO,
    ]
    df_zotero = df_zotero.assign(
        _match_doi=df_zotero[NAME_COL_DOI].map(normalize_doi),
        _match_title=df_zotero[NAME_COL_TITLE].astype(str).str.strip().str.lower(),
    ).drop_duplicates(subset=["_match_doi", "_match_title"], keep="first")

    df_merged = df_merged.assign(
        _match_doi=df_merged[NAME_COL_DOI].map(normalize_doi),
        _match_title=df_merged[NAME_COL_TITLE].astype(str).str.strip().str.lower(),
    )

    # Match by DOI
    df_doi = df_zotero[df_zotero["_match_doi"].notna()].drop(
        columns=[NAME_COL_DOI, NAME_COL_TITLE, "_match_title"]
    )
    df_merged = df_merged.merge(df_doi, how="left", on="_match_doi")

    # Fallback: match the rows still without metadata by title
    unmatched_mask = df_merged[NAME_COL_AUTHORS_ZOTERO].isna() & df_merged[
        "_match_title"
    ].notna()
    if unmatched_mask.any():
        df_title = df_zotero[df_zotero["_match_doi"].isna()].drop(
            columns=[NAME_COL_DOI, NAME_COL_TITLE, "_match_doi"]
        )
        # A DOI-less Zotero item is uniquely identified by its title
        df_merged.loc[unmatched_mask, zotero_columns] = (
            df_merged.loc[unmatched_mask]
            .drop(columns=zotero_columns, errors="ignore")
            .merge(df_title, how="left", on="_match_title", sort=False)[
                zotero_columns
            ]
            .to_numpy()
        )

    return df_merged.drop(columns=["_match_doi", "_match_title"])


def main(
    input_path: str | None = None,
    collection_name: str = "SLR-RAG",
    parent_collection_name: str | None = None,
    output_path: str | None = None,
):
    """Create the collection, upload the papers, query Zotero, update the DataFrame."""
    input_path = input_path or PATH_CSV_01_QUERY_RESULTS
    output_path = output_path or PATH_CSV_ZOTERO_QUERY_RESULTS

    df_papers = pd.read_csv(input_path)
    print(f"{len(df_papers)} papers loaded from {input_path}")

    zot = load_zotero_client()
    collection_key = create_collection(zot, collection_name, parent_collection_name)
    print(f"Collection '{collection_name}' created (key: {collection_key})")

    upload_papers_to_collection(zot, df_papers, collection_key)
    print("All papers uploaded.")

    df_zotero = fetch_collection_metadata(zot, collection_key)
    print(f"{len(df_zotero)} items retrieved from Zotero.")

    df_updated = update_dataframe_with_zotero(df_papers, df_zotero)
    df_updated.to_csv(output_path, index=False)
    print(f"Updated DataFrame saved to {output_path}")
    return df_updated


if __name__ == "__main__":
    main(collection_name="SLR-RAG", parent_collection_name=None)
