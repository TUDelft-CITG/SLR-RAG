import os
import re

import pandas as pd
from dotenv import load_dotenv
from tqdm import tqdm
from pyzotero import zotero
from pyzotero.zotero import Zotero
from slrrag.settings import (
    NAME_COL_AUTHORS_ZOTERO,
    NAME_COL_CONFERENCE_ZOTERO,
    NAME_COL_COUNTRY_ZOTERO,
    NAME_COL_DOI,
    NAME_COL_JOURNAL_ZOTERO,
    NAME_COL_TITLE,
    NAME_COL_UNIVERSITY_ZOTERO,
    PATH_CSV_01_QUERY_RESULTS,
    PATH_CSV_ZOTERO_QUERY_RESULTS,
    PROJECT_ROOT,
)

# Zotero write API accepts at most 50 items per request
ZOTERO_MAX_ITEMS_PER_REQUEST = 50

# Policies when a collection with the same name already exists
COLLECTION_IF_EXISTS_DO_NOTHING = "do nothing"
COLLECTION_IF_EXISTS_OVERWRITE = "overwrite"
COLLECTION_IF_EXISTS_ADD_NEW = "add new"
COLLECTION_IF_EXISTS_POLICIES = (
    COLLECTION_IF_EXISTS_DO_NOTHING,
    COLLECTION_IF_EXISTS_OVERWRITE,
    COLLECTION_IF_EXISTS_ADD_NEW,
)


def load_zotero_client():
    """Create a Zotero client from the credentials in PROJECT_ROOT/.env.

    Expected variables:
        ZOTERO_LIBRARY_ID=<numeric id>
        ZOTERO_API_KEY=<api key>
        ZOTERO_LIBRARY_TYPE=user   # or group
    """

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


def get_collection_key(zot: Zotero, name: str) -> str | None:
    """Return the key of the first collection whose name matches `name`."""
    for collection in zot.everything(zot.collections()):
        if collection["data"]["name"] == name:
            return collection["key"]
    return None


def create_collection(
    zot: Zotero,
    collection_name: str,
    parent_collection_name: str | None = None,
    if_exists: str = COLLECTION_IF_EXISTS_DO_NOTHING,
) -> str:
    """Create a collection (optionally nested inside a parent) and return its key.

    If a collection with the same name already exists, `if_exists` decides:
        - "do nothing": return the key of the existing collection unchanged
        - "overwrite": erase every paper inside, then return its key
        - "add new": keep its papers, then return its key
    """
    if if_exists not in COLLECTION_IF_EXISTS_POLICIES:
        raise ValueError(
            f"Invalid if_exists '{if_exists}', expected one of {COLLECTION_IF_EXISTS_POLICIES}."
        )

    existing_key = get_collection_key(zot, collection_name)
    if existing_key is not None:
        if if_exists == COLLECTION_IF_EXISTS_OVERWRITE:
            remove_collection_items(zot, existing_key)
        return existing_key

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


def remove_collection_items(zot: Zotero, collection_key: str):
    """Remove every paper from the collection (the items stay in the library)."""
    items = [
        item
        for item in zot.everything(zot.collection_items(collection_key))
        if item["data"]["itemType"] not in ("attachment", "note")
    ]
    for item in tqdm(items, desc="Removing papers from the collection"):
        zot.deletefrom_collection(collection_key, item)


def fetch_library_papers(zot: Zotero) -> list[dict]:
    """Return the API dict of every regular item of the Zotero library."""
    return [
        item
        for item in zot.everything(zot.items())
        if item["data"]["itemType"] not in ("attachment", "note")
    ]


def link_papers_to_collection(
    zot: Zotero, df_papers: pd.DataFrame, collection_key: str
) -> pd.DataFrame:
    """Add the papers already in the Zotero library to the collection, report the others.

    Papers are matched on normalized DOI first, then on normalized title.
    Matched items are added to the collection (items already in it are left
    as they are). Papers found nowhere in the library are printed at the end —
    their DOI to paste into the Zotero magic wand, then the title of those
    without a DOI to retrieve manually — and returned as a DataFrame.
    """
    by_doi, by_title = {}, {}
    for item in fetch_library_papers(zot):
        data = item["data"]
        doi = normalize_doi(data.get("DOI"))
        if doi and doi not in by_doi:
            by_doi[doi] = item
        title = data.get("title")
        if title and title.strip().lower() not in by_title:
            by_title[title.strip().lower()] = item

    in_collection = {
        item["key"] for item in zot.everything(zot.collection_items(collection_key))
    }

    to_add, unmatched = [], []
    for _, paper in df_papers.iterrows():
        item = by_doi.get(normalize_doi(paper.get(NAME_COL_DOI)))
        title = paper.get(NAME_COL_TITLE)
        if item is None and pd.notna(title):
            item = by_title.get(str(title).strip().lower())
        if item is None:
            unmatched.append(paper)
        elif item["key"] not in in_collection:
            to_add.append(item)
            in_collection.add(item["key"])

    for item in tqdm(to_add, desc="Linking papers to the collection"):
        zot.addto_collection(collection_key, item)
    print(f"{len(to_add)} existing item(s) added to the collection.")

    df_unmatched = pd.DataFrame(unmatched, columns=df_papers.columns)
    if not df_unmatched.empty:
        with_doi = df_unmatched[df_unmatched[NAME_COL_DOI].notna()]
        if not with_doi.empty:
            print(
                f"{len(with_doi)} paper(s) not in Zotero, DOI to paste in the magic wand:"
            )
            for doi in with_doi[NAME_COL_DOI]:
                print(f"  {doi}")
        without_doi = df_unmatched[df_unmatched[NAME_COL_DOI].isna()]
        if not without_doi.empty:
            print(
                f"{len(without_doi)} paper(s) not in Zotero and without a DOI, to retrieve manually:"
            )
            for title in without_doi[NAME_COL_TITLE]:
                print(f"  {title}")
    return df_unmatched


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


def fetch_collection_metadata(zot: Zotero, collection_key: str) -> pd.DataFrame:
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
    unmatched_mask = (
        df_merged[NAME_COL_AUTHORS_ZOTERO].isna() & df_merged["_match_title"].notna()
    )
    if unmatched_mask.any():
        df_title = df_zotero[df_zotero["_match_doi"].isna()].drop(
            columns=[NAME_COL_DOI, NAME_COL_TITLE, "_match_doi"]
        )
        # A DOI-less Zotero item is uniquely identified by its title
        df_merged.loc[unmatched_mask, zotero_columns] = (
            df_merged.loc[unmatched_mask]
            .drop(columns=zotero_columns, errors="ignore")
            .merge(df_title, how="left", on="_match_title", sort=False)[zotero_columns]
            .to_numpy()
        )

    return df_merged.drop(columns=["_match_doi", "_match_title"])


def main(
    input_path: str | None = None,
    collection_name: str = "SLR-RAG",
    parent_collection_name: str | None = None,
    output_path: str | None = None,
    if_exists: str = COLLECTION_IF_EXISTS_DO_NOTHING,
):
    """Create the collection, link the papers, query Zotero, update the DataFrame."""
    input_path = input_path or PATH_CSV_01_QUERY_RESULTS
    output_path = output_path or PATH_CSV_ZOTERO_QUERY_RESULTS

    df_papers = pd.read_csv(input_path)
    print(f"{len(df_papers)} papers loaded from {input_path}")

    zot = load_zotero_client()
    already_exists = get_collection_key(zot, collection_name) is not None
    collection_key = create_collection(
        zot, collection_name, parent_collection_name, if_exists=if_exists
    )
    if already_exists:
        print(f"Collection '{collection_name}' already exists (key: {collection_key})")
    else:
        print(f"Collection '{collection_name}' created (key: {collection_key})")

    if already_exists and if_exists == COLLECTION_IF_EXISTS_DO_NOTHING:
        print(f"if_exists='{if_exists}': no paper linked.")
    else:
        link_papers_to_collection(zot, df_papers, collection_key)

    df_zotero = fetch_collection_metadata(zot, collection_key)
    print(f"{len(df_zotero)} items retrieved from Zotero.")

    df_updated = update_dataframe_with_zotero(df_papers, df_zotero)
    df_updated.to_csv(output_path, index=False)
    print(f"Updated DataFrame saved to {output_path}")
    return df_updated


if __name__ == "__main__":
    main(collection_name="SLR-RAG", parent_collection_name=None)
