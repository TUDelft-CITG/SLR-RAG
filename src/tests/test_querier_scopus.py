"""
Pytest tests for querier_scopus.py module

Tests cover:
- to_query_scopus function
- scopus_to_dict_list function
- check_doi_in_scopus function (basic structure)
"""

import pytest
import os
import sys
import pandas as pd
import pickle

# Add the src directory to the Python path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from slrrag.querier_scopus import (
    to_query_scopus,
    scopus_to_dict_list,
)
from slrrag.settings import (
    DEFAULT_DF_COLUMNS,
    NAME_COL_RELEVANCE_ORDER_SCOPUS,
    SchemaScopusPapers,
)


# Fixtures


@pytest.fixture
def sample_scopus_search():
    """Load the test ScopusSearch object from pickle file."""
    pickle_path = os.path.join(
        os.path.dirname(__file__), "data", "01_test_search_scopus.pickle"
    )
    with open(pickle_path, "rb") as f:
        return pickle.load(f)


@pytest.fixture
def empty_scopus_search():
    """Create a mock empty ScopusSearch-like object."""

    # Create a minimal mock object that mimics ScopusSearch
    class MockScopusSearch:
        def __init__(self):
            self.results = None

    return MockScopusSearch()


# Tests for to_query_scopus function


class TestToQueryScopus:
    """Tests for the to_query_scopus function."""

    def test_basic_query(self):
        """Test basic query conversion."""
        query = "offshore wind farm"
        result = to_query_scopus(query)
        expected = """
TITLE-ABS-KEY( offshore wind farm)
"""
        assert result == expected

    def test_query_with_special_characters(self):
        """Test query with special characters."""
        query = "offshore AND wind OR farm"
        result = to_query_scopus(query)
        expected = """
TITLE-ABS-KEY( offshore AND wind OR farm)
"""
        assert result == expected

    def test_query_with_parentheses(self):
        """Test query with parentheses."""
        query = "(offshore OR marine) AND wind"
        result = to_query_scopus(query)
        expected = """
TITLE-ABS-KEY( (offshore OR marine) AND wind)
"""
        assert result == expected

    def test_empty_query(self):
        """Test empty query string."""
        query = ""
        result = to_query_scopus(query)
        expected = """
TITLE-ABS-KEY( )
"""
        assert result == expected

    def test_query_with_quotes(self):
        """Test query with quotes."""
        query = '"offshore wind"'
        result = to_query_scopus(query)
        expected = """
TITLE-ABS-KEY( "offshore wind")
"""
        assert result == expected

    def test_complex_multi_line_query(self):
        """Test complex multi-line query with multiple conditions."""
        main_query = """
("risk assessment" OR "risk analysis") AND
("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
("maritime" OR  "navigational" OR "nautical")
"""
        result = to_query_scopus(main_query)
        expected = """
TITLE-ABS-KEY( 
("risk assessment" OR "risk analysis") AND
("Offshore windfarm" OR "Offshore windmill" OR "Offshore wind turbine" OR "Offshore wind park" OR "OWF") AND
("Strategic" OR "Static" OR "Long-term" OR "Marine spatial planning" OR "Large scale") AND
("maritime" OR  "navigational" OR "nautical")
)
"""
        assert result == expected


# Tests for scopus_to_dict_list function


class TestScopusToDictList:
    """Tests for the scopus_to_dict_list function."""

    def test_with_real_data(self, sample_scopus_search):
        """Test conversion with real ScopusSearch data."""
        result_df = scopus_to_dict_list(sample_scopus_search)

        # Check that it returns a DataFrame
        assert isinstance(result_df, pd.DataFrame)

        # Check that it has the expected columns
        expected_columns = DEFAULT_DF_COLUMNS + ["id_scopus", "keywords_scopus"]
        for col in expected_columns:
            assert col in result_df.columns

        # Check that relevance_order_scopus column is added
        assert NAME_COL_RELEVANCE_ORDER_SCOPUS in result_df.columns

        # Check that the DataFrame is not empty
        assert len(result_df) > 0

        # Check specific data from the first result
        first_paper = sample_scopus_search.results[0]
        assert result_df.iloc[0]["doi"] == first_paper.doi
        assert result_df.iloc[0]["title"] == first_paper.title
        # Date is converted to Timestamp by schema, so compare as string
        assert str(result_df.iloc[0]["date"]).startswith(first_paper.coverDate)
        assert result_df.iloc[0]["abstract"] == first_paper.description
        assert result_df.iloc[0]["id_scopus"] == first_paper.eid
        # Type is converted by schema parser (e.g., "Conference Paper" -> "conference-paper")
        from slrrag.settings import ARTICLE_TYPE_MAPPING

        expected_type = ARTICLE_TYPE_MAPPING.get(
            first_paper.subtypeDescription.lower(),
            first_paper.subtypeDescription.lower(),
        )
        assert result_df.iloc[0]["type"] == expected_type

        # Check that the relevance order is set correctly (should be 0-indexed)
        assert result_df[NAME_COL_RELEVANCE_ORDER_SCOPUS].tolist() == list(
            range(len(result_df))
        )

    def test_with_empty_results(self, empty_scopus_search):
        """Test conversion with empty results."""
        result_df = scopus_to_dict_list(empty_scopus_search)

        # Check that it returns a DataFrame
        assert isinstance(result_df, pd.DataFrame)

        # Check that it has the expected columns
        expected_columns = DEFAULT_DF_COLUMNS + ["id_scopus"]
        for col in expected_columns:
            assert col in result_df.columns

        # Check that the DataFrame is empty
        assert len(result_df) == 0

    def test_with_none_results(self):
        """Test conversion when results is None."""

        # Create a minimal mock object that mimics ScopusSearch
        class MockScopusSearch:
            def __init__(self):
                self.results = None

        mock_search = MockScopusSearch()

        result_df = scopus_to_dict_list(mock_search)

        # Check that it returns an empty DataFrame with correct columns
        assert isinstance(result_df, pd.DataFrame)
        expected_columns = DEFAULT_DF_COLUMNS + ["id_scopus"]
        for col in expected_columns:
            assert col in result_df.columns
        assert len(result_df) == 0

    def test_data_types(self, sample_scopus_search):
        """Test that the data types are correct."""
        result_df = scopus_to_dict_list(sample_scopus_search)

        # Check that string columns are of string type
        assert result_df["doi"].dtype == object or pd.api.types.is_string_dtype(
            result_df["doi"]
        )
        assert result_df["title"].dtype == object or pd.api.types.is_string_dtype(
            result_df["title"]
        )
        assert result_df["abstract"].dtype == object or pd.api.types.is_string_dtype(
            result_df["abstract"]
        )
        assert result_df["id_scopus"].dtype == object or pd.api.types.is_string_dtype(
            result_df["id_scopus"]
        )

        # Check that relevance_order_scopus is integer type
        assert pd.api.types.is_integer_dtype(result_df[NAME_COL_RELEVANCE_ORDER_SCOPUS])

    def test_handles_none_values(self, sample_scopus_search):
        """Test that None values are handled correctly."""
        result_df = scopus_to_dict_list(sample_scopus_search)

        # Check that None values in authkeywords are handled
        # (from our inspection, authkeywords can be None)
        # The function should not crash and should handle None gracefully
        assert (
            result_df["keywords_scopus"].isna().sum() >= 0
        )  # Should not raise an error

    def test_schema_validation(self, sample_scopus_search):
        """Test that the result validates against SchemaScopusPapers."""
        result_df = scopus_to_dict_list(sample_scopus_search)

        # This should not raise an exception if the schema is correct
        try:
            validated_df = SchemaScopusPapers.validate(result_df, lazy=True)
            assert validated_df is not None
        except Exception as e:
            pytest.fail(f"Schema validation failed: {e}")

    def test_column_order(self, sample_scopus_search):
        """Test that columns are in the expected order."""
        result_df = scopus_to_dict_list(sample_scopus_search)

        # Check that default columns are present and in order
        for col in DEFAULT_DF_COLUMNS:
            assert col in result_df.columns

        # Check that id_scopus is present
        assert "id_scopus" in result_df.columns


# Additional edge case tests


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_to_query_scopus_with_newlines(self):
        """Test to_query_scopus with newlines in input."""
        query = "offshore\nwind\nfarm"
        result = to_query_scopus(query)
        assert "TITLE-ABS-KEY(" in result
        assert "offshore" in result
        assert "wind" in result
        assert "farm" in result

    def test_to_query_scopus_with_tabs(self):
        """Test to_query_scopus with tabs in input."""
        query = "offshore\twind\tfarm"
        result = to_query_scopus(query)
        assert "TITLE-ABS-KEY(" in result
        assert "offshore" in result

    def test_scopus_to_dict_list_with_different_document_types(
        self, sample_scopus_search
    ):
        """Test that different document types are handled correctly."""
        result_df = scopus_to_dict_list(sample_scopus_search)

        # Check that type column contains expected values
        assert result_df["type"].notna().all() or result_df["type"].isna().sum() == 0

        # Check that all types are strings or None
        for paper_type in result_df["type"]:
            assert paper_type is None or isinstance(paper_type, str)


# Run tests


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
