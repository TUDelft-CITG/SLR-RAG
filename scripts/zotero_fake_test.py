"""Small end-to-end test of the Zotero pipeline with a fake DataFrame.

By default, the pipeline runs against an in-memory fake Zotero client:
no network, no credentials, nothing written to a real library. The fake
client also simulates the metadata resolution that the Zotero desktop
client would do on the uploaded items (authors, journal, university...).

Use --real to run against your actual Zotero library (requires
ZOTERO_LIBRARY_ID / ZOTERO_API_KEY in the .env file, and `pip install
pyzotero`). It will create a collection "SLR-RAG-TEST" and upload the
5 fake papers into it.

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
    load_zotero_client,
    update_dataframe_with_zotero,
    upload_papers_to_collection,
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

    Implements only the methods used by querier_zotero. On item creation,
    it simulates the metadata resolution of the Zotero desktop client,
    so the query step has authors, journal, university... to return.
    """

    FAKE_AUTHORS = [
        ("Alice", "Dupont"),
        ("Bob", "Smith"),
        ("Chen", "Wei"),
        ("Dana", "Ivanova"),
    ]

    def __init__(self):
        self.collections_data = {}
        self.items_data = {}
        self._counter = 0

    def _next_key(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}{self._counter}"

    # --- Templates (subset of the real item templates) ---
    def item_template(self, item_type: str) -> dict:
        common = {"itemType": item_type, "title": "", "creators": []}
        per_type = {
            "journalArticle": {
                "DOI": "",
                "abstractNote": "",
                "date": "",
                "publicationTitle": "",
            },
            "conferencePaper": {
                "DOI": "",
                "abstractNote": "",
                "date": "",
                "proceedingsTitle": "",
                "place": "",
            },
            "preprint": {"DOI": "", "abstractNote": "", "date": ""},
            "thesis": {
                "abstractNote": "",
                "date": "",
                "university": "",
                "place": "",
            },
        }
        return {**common, **per_type.get(item_type, {}), "itemType": item_type}

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
    def create_items(self, items: list) -> dict:
        resp = {"success": {}, "failed": {}}
        for i, data in enumerate(items):
            key = self._next_key("ITEM")
            # Simulate metadata resolution done by the Zotero desktop client
            data["creators"] = [
                {"creatorType": "author", "firstName": first, "lastName": last}
                for first, last in self.FAKE_AUTHORS[: 1 + i % len(self.FAKE_AUTHORS)]
            ]
            if data["itemType"] == "journalArticle":
                data["publicationTitle"] = f"Journal of Fake Studies, vol {i + 1}"
            elif data["itemType"] == "conferencePaper":
                data["proceedingsTitle"] = f"Proceedings of FAKECONF {2022 + i}"
                data["place"] = "Grenoble, France"
            elif data["itemType"] == "thesis":
                data["university"] = "Universite Grenoble Alpes"
                data["place"] = "Grenoble, France"
            self.items_data[key] = {"data": data}
            resp["success"][str(i)] = key
        return resp

    def collection_items(self, collection_key: str) -> list:
        return [
            item
            for item in self.items_data.values()
            if collection_key in item["data"].get("collections", [])
        ]

    # pyzotero paginates and returns everything; here everything is a no-op
    def everything(self, results):
        return results


def run_pipeline(zot) -> pd.DataFrame:
    df_papers = make_fake_dataframe()
    print(f"Fake DataFrame: {len(df_papers)} papers")

    collection_key = create_collection(zot, COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' created (key: {collection_key})")

    upload_papers_to_collection(zot, df_papers, collection_key)

    df_zotero = fetch_collection_metadata(zot, collection_key)
    print(f"{len(df_zotero)} items retrieved from Zotero")

    df_updated = update_dataframe_with_zotero(df_papers, df_zotero)
    return df_updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--real",
        action="store_true",
        help="Upload to your real Zotero library instead of the simulation",
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
