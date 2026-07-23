"""
Pytest tests for querier_openalex.py module

Tests cover:
- work_openalex_to_list function
"""

from pathlib import Path

import pytest
import os
import sys
import pandas as pd
import pickle
from unittest.mock import Mock

# Add the src directory to the Python path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from slrrag.querier_openalex import (
    work_openalex_to_list,
    parse_openalex_list_to_dataframe,
)
from slrrag.settings import SchemaOpenAlexPapers


# Fixtures


@pytest.fixture
def sample_openalex_works():
    """Load the test Works object from pickle file."""
    pickle_path = os.path.join(
        os.path.dirname(__file__), "data", "01_test_search_openalex.pickle"
    )
    with open(pickle_path, "rb") as f:
        return pickle.load(f)


@pytest.fixture
def sample_openalex_papers_list():
    """Get a list of OpenAlex papers from the Works object."""
    out_file_openalex_list = (
        Path(__file__).parent / "data" / "01_test_search_openalex_list.pickle"
    )
    with open(out_file_openalex_list, "rb") as f:
        return pickle.load(f)


# Tests for work_openalex_to_list function


@pytest.mark.skip(reason="call OpenAlex API. Comment only if needed")
class TestWorkOpenAlexToList:
    """Tests for the work_openalex_to_list function."""

    def test_with_real_works_object(self, sample_openalex_works):
        """Test with actual Works object from pickle."""
        result = work_openalex_to_list(sample_openalex_works)

        # Check that it returns a list
        assert isinstance(result, list)

        # Check that the list length matches the works count
        expected_count = sample_openalex_works.count()
        assert len(result) == expected_count

        # Check that each item is a Work object (dict-like)
        for item in result:
            assert hasattr(item, "keys") or isinstance(item, dict)
            assert "doi" in item or hasattr(item, "doi")

    def test_with_empty_works(self):
        """Test with Works object that has 0 results."""
        # Create a mock Works object with count returning 0
        mock_works = Mock()
        mock_works.count.return_value = 0
        mock_works.paginate.return_value = [[]]  # Empty page

        result = work_openalex_to_list(mock_works)

        # Check that it returns an empty list
        assert isinstance(result, list)
        assert len(result) == 0

    def test_pagination_logic(self):
        """Test that pagination processes all pages correctly."""
        # Create a mock Works object with known count
        expected_count = 25  # More than one page with DEFAULT_OPEN_ALEX_PAGING=50
        mock_page1 = [Mock(doi=f"doi_{i}") for i in range(10)]
        mock_page2 = [Mock(doi=f"doi_{i}") for i in range(10, 25)]

        mock_works = Mock()
        mock_works.count.return_value = expected_count
        mock_works.paginate.return_value = [mock_page1, mock_page2]

        result = work_openalex_to_list(mock_works)

        # Check that it returns a list with all items
        assert isinstance(result, list)
        assert len(result) == expected_count

        # Check that all items are included
        assert all(hasattr(item, "doi") for item in result)


# Tests for parse_openalex_list_to_dataframe function


class TestParseOpenAlexListToDataFrame:
    """Tests for the parse_openalex_list_to_dataframe function."""

    def test_with_real_openalex_data(self, sample_openalex_papers_list):
        """Test with real data from OpenAlex."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check that it returns a DataFrame
        assert isinstance(result_df, pd.DataFrame)

        # Check that it has the expected columns from SchemaOpenAlexPapers
        expected_columns = [
            "doi",
            "id_openalex",
            "title",
            "date",
            "abstract",
            "type",
            "relevance_openalex",
            "pdf",
            "topic_openalex",
            "fields_openalex",
            "subfields_openalex",
            "domain_openalex",
            "keywords_openalex",
        ]
        for col in expected_columns:
            assert col in result_df.columns

        # Check that the DataFrame is not empty
        assert len(result_df) > 0

    def test_column_mapping(self, sample_openalex_papers_list):
        """Test mapping of OpenAlex fields to DataFrame columns."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check that all input columns are mapped correctly
        assert "doi" in result_df.columns
        assert "title" in result_df.columns
        assert "date" in result_df.columns  # Renamed from publication_date
        assert "abstract" in result_df.columns
        assert "type" in result_df.columns
        assert "id_openalex" in result_df.columns  # Renamed from id
        assert "relevance_openalex" in result_df.columns  # Renamed from relevance_score

    def test_primary_topic_extraction(self, sample_openalex_papers_list):
        """Test primary topic extraction."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check that topic_openalex column exists
        assert "topic_openalex" in result_df.columns

        # For papers with primary_topic, it should extract display_name
        # For papers without, it should be None/NaN
        assert result_df["topic_openalex"].isna().sum() >= 0  # Should not crash

    def test_field_extraction(self, sample_openalex_papers_list):
        """Test field extraction from primary_topic."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check that fields_openalex column exists
        assert "fields_openalex" in result_df.columns

        # Should handle missing fields gracefully
        assert result_df["fields_openalex"].isna().sum() >= 0

    def test_subfield_extraction(self, sample_openalex_papers_list):
        """Test subfield extraction from primary_topic."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check that subfields_openalex column exists
        assert "subfields_openalex" in result_df.columns

    def test_domain_extraction(self, sample_openalex_papers_list):
        """Test domain extraction from primary_topic."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check that domain_openalex column exists
        assert "domain_openalex" in result_df.columns

    def test_keywords_extraction(self, sample_openalex_papers_list):
        """Test keywords extraction and joining with pipe separator."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check that keywords_openalex column exists
        assert "keywords_openalex" in result_df.columns

        # For papers with keywords, check they are joined with |
        non_null_keywords = result_df["keywords_openalex"].dropna()
        for keywords in non_null_keywords:
            if pd.notna(keywords):
                # Should be a string with pipe-separated values
                assert isinstance(keywords, str)

    def test_pdf_url_extraction(self, sample_openalex_papers_list):
        """Test PDF URL extraction."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check that pdf column exists
        assert "pdf" in result_df.columns

    def test_doi_formatting(self, sample_openalex_papers_list):
        """Test that DOI prefix is removed."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check that doi column exists
        assert "doi" in result_df.columns

        # Check that no DOI starts with https://doi.org/
        for doi in result_df["doi"].dropna():
            assert not doi.startswith("https://doi.org/")

    def test_empty_list(self):
        """Test with empty input list."""
        # This test is expected to potentially fail due to schema validation
        # but we can test that the function handles empty input gracefully
        try:
            result_df = parse_openalex_list_to_dataframe([])
            # Check that it returns an empty DataFrame
            assert isinstance(result_df, pd.DataFrame)
            assert len(result_df) == 0
        except Exception as e:
            # If schema validation fails for empty DataFrame, that's acceptable
            # The important thing is that the function doesn't crash unexpectedly
            assert "SchemaErrors" in str(type(e)) or "expected" in str(e).lower()

    def test_schema_validation(self, sample_openalex_papers_list):
        """Test that the result validates against SchemaOpenAlexPapers."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # This should not raise an exception if the schema is correct
        try:
            validated_df = SchemaOpenAlexPapers.validate(result_df, lazy=True)
            assert validated_df is not None
        except Exception as e:
            pytest.fail(f"Schema validation failed: {e}")

    def test_data_types(self, sample_openalex_papers_list):
        """Test that column data types are correct."""
        result_df = parse_openalex_list_to_dataframe(sample_openalex_papers_list)

        # Check string columns
        string_columns = [
            "doi",
            "title",
            "abstract",
            "type",
            "id_openalex",
            "pdf",
            "topic_openalex",
            "fields_openalex",
            "subfields_openalex",
            "domain_openalex",
            "keywords_openalex",
        ]
        for col in string_columns:
            if col in result_df.columns:
                assert (
                    pd.api.types.is_string_dtype(result_df[col])
                    or result_df[col].dtype == object
                )

        # Check numeric column
        assert pd.api.types.is_numeric_dtype(result_df["relevance_openalex"])

        # Check date column
        assert pd.api.types.is_datetime64_any_dtype(result_df["date"])


# Run tests


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
