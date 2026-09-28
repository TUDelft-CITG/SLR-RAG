"""Small end-to-end test of the Zotero pipeline with a fake library.

By default, the pipeline runs against an in-memory fake Zotero client:
no network, no credentials, nothing written to a real library. The fake
library is pre-populated with richly-described items, as if they had
been added by hand with the Zotero desktop client (magic wand), so the
query step has authors, journal, university... to return.

Use --real to run against your actual Zotero library (requires
ZOTERO_LIBRARY_ID / ZOTERO_API_KEY in the .env file). It will create a
collection "SLR-RAG-TEST" and link the fake papers already present in
the library; the missing ones are only printed for the magic wand,
nothing is uploaded.

Usage:
    python scripts/zotero_fake_test.py            # simulation
    python scripts/zotero_fake_test.py --real     # real library
"""

import argparse
import sys

import pandas as pd
from pandera.typing import DataFrame

from slrrag.querier_zotero import (
    create_collection,
    fetch_collection_metadata,
    link_papers_to_collection,
    load_zotero_client,
    update_dataframe_with_zotero,
)
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
    PATH_CSV_ZOTERO_QUERY_RESULTS,
    SchemaPapers,
    PANDERA_LAZY_VALIDATION,
)

COLLECTION_NAME = "SLR-RAG-TEST"

ZOTERO_COLUMNS = [
    NAME_COL_AUTHORS_ZOTERO,
    NAME_COL_JOURNAL_ZOTERO,
    NAME_COL_CONFERENCE_ZOTERO,
    NAME_COL_UNIVERSITY_ZOTERO,
    NAME_COL_COUNTRY_ZOTERO,
]


def make_fake_dataframe() -> DataFrame[SchemaPapers]:
    df = pd.DataFrame(
        {
            NAME_COL_DOI: [
                "10.1000/fake.2023.001",
                "10.1000/fake.2023.002",
                None,  # no DOI -> matched by title at merge time
                "10.1000/fake.2024.003",
                "10.1000/fake.2024.004",
            ],
            NAME_COL_TITLE: [
                "Retrieval-augmented generation for systematic reviews",
                "Large language models in the scientific pipeline",
                "A workshop paper without a DOI",
                "Distributed training of language models",
                "Thesis on literature-based discovery",
            ],
            NAME_COL_DATE: [
                "2023-05-01",
                "2023-11-15",
                "2022-06-01",
                "2024-02-01",
                "2024-09-20",
            ],
            NAME_COL_ABSTRACT: [
                "We study how RAG helps systematic literature reviews.",
                "An overview of LLM usage in scientific workflows.",
                "A short workshop paper about SLR tooling.",
                "Scaling laws for distributed training.",
                "A dissertation on knowledge discovery from publications.",
            ],
            NAME_COL_TYPE: [
                "article",
                "article",
                "conference-paper",
                "preprint",
                "dissertation",
            ],
        }
    )
    return SchemaPapers.validate(df, lazy=PANDERA_LAZY_VALIDATION)


class FakeZotero:
    """Minimal in-memory stand-in for pyzotero.Zotero.

    Implements only the methods used by querier_zotero. The library is
    pre-populated by seed_fake_library(), as if the papers had been added
    by the Zotero desktop client; linking an item only adds the collection
    to its membership, it never creates items.
    """

    def __init__(self):
        self.collections_data = {}
        self.items_data = {}
        self._counter = 0

    def _next_key(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}{self._counter}"

    # --- Collections ---
    def collections(self):
        return [
            {"key": key, "data": data} for key, data in self.collections_data.items()
        ]

    def create_collections(self, payload: list) -> dict:
        resp = {"success": {}, "failed": {}}
        for i, collection in enumerate(payload):
            key = self._next_key("COLL")
            self.collections_data[key] = {
                "name": collection["name"],
                "parentCollection": collection.get("parentCollection"),
            }
            resp["success"][str(i)] = key
        return resp

    # --- Items ---
    def add_library_item(self, data: dict):
        key = self._next_key("ITEM")
        data.setdefault("collections", [])
        self.items_data[key] = {"key": key, "version": 1, "data": data}

    def items(self) -> list:
        return list(self.items_data.values())

    def collection_items(self, collection_key: str) -> list:
        return [
            item
            for item in self.items_data.values()
            if collection_key in item["data"].get("collections", [])
        ]

    def addto_collection(self, collection_key: str, payload: dict):
        item = self.items_data[payload["key"]]
        if collection_key not in item["data"]["collections"]:
            item["data"]["collections"].append(collection_key)
            item["version"] += 1

    def deletefrom_collection(self, collection_key: str, payload: dict):
        item = self.items_data[payload["key"]]
        item["data"]["collections"] = [
            c for c in item["data"]["collections"] if c != collection_key
        ]
        item["version"] += 1

    # pyzotero paginates and returns everything; here everything is a no-op
    def everything(self, results):
        return results


def seed_fake_library(zot, df_papers) -> None:
    """Pre-populate the fake library as if the papers had been added by hand."""
    paper = df_papers.iloc

    # Paper 0: exact DOI match, rich journalArticle metadata
    zot.add_library_item(
        {
            "itemType": "journalArticle",
            "title": paper[0][NAME_COL_TITLE],
            "DOI": paper[0][NAME_COL_DOI],
            "creators": [
                {"creatorType": "author", "firstName": "Alice", "lastName": "Dupont"},
                {"creatorType": "author", "firstName": "Bob", "lastName": "Smith"},
            ],
            "publicationTitle": "Journal of Fake Studies, vol 1",
        }
    )
    # Paper 1: DOI match even though the stored title differs
    zot.add_library_item(
        {
            "itemType": "journalArticle",
            "title": paper[1][NAME_COL_TITLE].upper(),
            "DOI": paper[1][NAME_COL_DOI],
            "creators": [
                {"creatorType": "author", "firstName": "Chen", "lastName": "Wei"},
            ],
            "publicationTitle": "Journal of Fake Studies, vol 2",
        }
    )
    # Paper 3: title match, no DOI in the library
    zot.add_library_item(
        {
            "itemType": "preprint",
            "title": f"  {paper[3][NAME_COL_TITLE]}  ",
            "creators": [
                {"creatorType": "author", "firstName": "Dana", "lastName": "Ivanova"},
            ],
        }
    )


def run_pipeline(zot) -> pd.DataFrame:
    df_papers = make_fake_dataframe()
    print(f"Fake DataFrame: {len(df_papers)} papers")

    simulation = isinstance(zot, FakeZotero)
    if simulation:
        seed_fake_library(zot, df_papers)
        print(f"Fake library: {len(zot.items())} items")
        library_size = len(zot.items())

    collection_key = create_collection(zot, COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' created (key: {collection_key})")

    df_unmatched = link_papers_to_collection(zot, df_papers, collection_key)

    if simulation:
        assert len(zot.items()) == library_size, "linking must not create items"
        assert len(df_unmatched) == 2, df_unmatched
        assert df_unmatched[NAME_COL_TITLE].tolist() == [
            "A workshop paper without a DOI",
            "Thesis on literature-based discovery",
        ], df_unmatched

    df_zotero = fetch_collection_metadata(zot, collection_key)
    print(f"{len(df_zotero)} items retrieved from Zotero")

    df_updated = update_dataframe_with_zotero(df_papers, df_zotero)
    return df_updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--real",
        action="store_true",
        help="Link to your real Zotero library instead of the simulation",
    )
    args = parser.parse_args()

    if args.real:
        zot = load_zotero_client()
    else:
        print("Simulation mode (use --real for the actual library)")
        zot = FakeZotero()

    df_updated = run_pipeline(zot)

    print("\nResulting DataFrame (Zotero columns):")
    print(df_updated[[NAME_COL_DOI, NAME_COL_TITLE] + ZOTERO_COLUMNS].to_string())

    if args.real:
        df_updated.to_csv(PATH_CSV_ZOTERO_QUERY_RESULTS, index=False)
        print(f"\nSaved to {PATH_CSV_ZOTERO_QUERY_RESULTS}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
