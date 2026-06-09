"""
Pytest tests for paper_review_tools.py module

Tests cover:
- sanitize_filename function
- slugify function
- format_field_value function
- get_field_group function
- highlight_keywords_in_text function
- write_paper_to_markdown function
- write_paper_into_markdown function
- update_paper_review_status function
"""

import pytest
import os
import sys
import tempfile
import pandas as pd

# Add the src directory to the Python path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from slrrag.convertmarkdown.paper_review_tools import (
    MANUAL_REVIEW_FIELD,
    slugify,
    write_series_papers_into_markdown,
    write_paper_to_markdown,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_output_file():
    """Create a temporary output directory."""
    with tempfile.NamedTemporaryFile() as temp_file:
        yield temp_file.name


@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_paper_dict():
    """Create a sample paper dictionary for testing."""
    return {
        "title": "Offshore Wind Farm Risk Assessment",
        "abstract": "This paper discusses collision risks in offshore wind farms and how to assess them.",
        "doi": "10.1234/abc",
        "year": "2023",
        "type": "journal-article",
        "pdf": "https://example.com/paper.pdf",
        "keywords_scopus": "offshore|wind farm|risk",
        "in_scopus": True,
        MANUAL_REVIEW_FIELD: None,
    }


@pytest.fixture
def sample_paper_with_all_fields():
    """Create a sample paper with all possible fields."""
    return {
        "title": "Advanced Offshore Infrastructure",
        "abstract": "Study of wind turbine and collision avoidance in maritime environments.",
        "doi": "10.5678/xyz",
        "year": "2024",
        "date": "2024-01-15",
        "type": "conference-paper",
        "pdf": "https://example.com/advanced.pdf",
        "id_scopus": "12345",
        "id_openalex": "A12345",
        "keywords_scopus": "offshore|infrastructure|collision",
        "relevance_order_scopus": "0.95",
        "in_scopus": True,
        "topic_openalex": "Engineering|Energy",
        "fields_openalex": "Marine Engineering|Renewable Energy",
        "keywords_openalex": "wind farm|risk assessment",
        "relevance_openalex": "0.87",
        "in_openalex": True,
        "topic_lens": "Infrastructure|Safety",
        "keywords_lens": "offshore|maritime",
        "in_lens": True,
        "topic_dimensions": "Energy|Transportation",
        "keywords_dimensions": "wind energy|ship",
        "in_dimensions": True,
        "is_found": True,
        "is_reference": False,
        MANUAL_REVIEW_FIELD: "keep",
    }


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame with multiple papers."""
    data = [
        {
            "title": "Paper One",
            "abstract": "About offshore wind farms.",
            "doi": "10.001/one",
            MANUAL_REVIEW_FIELD: None,
        },
        {
            "title": "Paper Two",
            "abstract": "Maritime collision risks.",
            "doi": "10.002/two",
            MANUAL_REVIEW_FIELD: "keep",
        },
        {
            "title": "Paper Three",
            "abstract": "No relevant keywords here.",
            "doi": "10.003/three",
            MANUAL_REVIEW_FIELD: "removed",
        },
    ]
    return pd.DataFrame(data)


# =============================================================================
# Tests for slugify function
# =============================================================================


class TestSlugify:
    """Tests for the slugify function."""

    def test_basic_title(self):
        """Test slugification of a basic title."""
        result = slugify("Offshore Wind Farms")
        assert result == "offshore-wind-farms"

    def test_lowercase_conversion(self):
        """Test that slug is lowercase."""
        result = slugify("UPPER CASE TITLE")
        assert result == "upper-case-title"
        assert result.islower()

    def test_special_characters_removed(self):
        """Test that special characters are removed."""
        result = slugify("Title/with:special*chars?")
        assert "/" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
        assert result == "titlewithspecialchars"

    def test_colon_removal(self):
        """Test that colons are removed."""
        result = slugify("Title: A Subtitle")
        assert ":" not in result
        assert result == "title-a-subtitle"

    def test_dashes(self):
        """Test handling of dashes."""
        result = slugify("Title \u2013 with \u2014 dashes")
        assert "\u2013" not in result
        assert "\u2014" not in result
        assert result == "title-with-dashes"

    def test_spaces_to_hyphens(self):
        """Test that spaces are converted to hyphens."""
        result = slugify("Title with spaces")
        assert result == "title-with-spaces"

    def test_multiple_spaces(self):
        """Test that multiple spaces are collapsed to single hyphens."""
        result = slugify("Title   with   multiple    spaces")
        assert "  " not in result
        assert "---" not in result
        assert result == "title-with-multiple-spaces"

    def test_empty_title(self):
        """Test handling of empty title."""
        result = slugify("")
        assert result == "untitled"

    def test_none_title(self):
        """Test handling of None title."""
        result = slugify(None)
        assert result == "untitled"

    def test_na_title(self):
        """Test handling of pd.NA title."""
        result = slugify(pd.NA)
        assert result == "untitled"

    def test_leading_trailing_hyphens(self):
        """Test that leading/trailing hyphens are removed."""
        result = slugify("---Title---")
        assert not result.startswith("-")
        assert not result.endswith("-")
        assert result == "title"

    def test_long_title(self):
        """Test that long titles are truncated."""
        long_title = "A " * 100  # 200 characters
        result = slugify(long_title, limit=150)
        assert len(result) <= 150

    def test_title_with_brackets(self):
        """Test handling of brackets."""
        result = slugify("Title (with) [brackets]")
        assert "(" not in result
        assert ")" not in result
        assert "[" not in result
        assert "]" not in result
        assert result == "title-with-brackets"

    def test_title_with_curly_braces(self):
        """Test handling of curly braces."""
        result = slugify("Title {with} curly {braces}")
        assert "{" not in result
        assert "}" not in result
        assert result == "title-with-curly-braces"

    def test_complex_title(self):
        """Test a complex title with various special characters."""
        result = slugify("The Impact of AI: A Comprehensive Analysis (2024)")
        assert result == "the-impact-of-ai-a-comprehensive-analysis-2024"

    def test_filename_usage(self):
        """Test that slug is suitable for filenames."""
        result = slugify("Test Title")
        filename = result + ".md"
        assert filename == "test-title.md"


# =============================================================================
# Tests for write_paper_to_markdown function
# =============================================================================


class TestWritePaperToMarkdown:
    """Tests for the write_paper_to_markdown function."""

    def test_creates_file(self, temp_output_file, sample_paper_dict):
        """Test that a file is created."""
        filepath = write_paper_to_markdown(
            sample_paper_dict, output_file=temp_output_file
        )
        assert os.path.exists(filepath)

    def test_file_contains_title(self, temp_output_file, sample_paper_dict):
        """Test that the file contains the title."""
        filepath = write_paper_to_markdown(
            sample_paper_dict, output_file=temp_output_file
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Title is now highlighted, so check for the highlighted version
        assert '# <span class="kw-offshore">Offshore</span>' in content
        assert '<span class="kw-wind-farm">Wind Farm</span>' in content
        assert '<span class="kw-risk">Risk</span>' in content
        assert '<span class="kw-assess">Assessment</span>' in content

    def test_file_contains_abstract(self, temp_output_file, sample_paper_dict):
        """Test that the file contains the abstract."""
        filepath = write_paper_to_markdown(
            sample_paper_dict, output_file=temp_output_file
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "## Abstract" in content
        # Abstract is now highlighted, so check for highlighted keywords
        assert '<span class="kw-collision">collision</span>' in content
        assert '<span class="kw-risk">risks</span>' in content
        assert '<span class="kw-offshore">offshore</span>' in content
        assert '<span class="kw-wind-farm">wind farms</span>' in content
        assert '<span class="kw-assess">assess</span>' in content

    def test_file_contains_doi(self, temp_output_file, sample_paper_dict):
        """Test that the file contains the DOI in frontmatter."""
        filepath = write_paper_to_markdown(
            sample_paper_dict, output_file=temp_output_file
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # DOI is now in frontmatter
        assert 'doi: "10.1234/abc"' in content

    def test_yaml_frontmatter(self, temp_output_file, sample_paper_dict):
        """Test that YAML frontmatter is included."""
        filepath = write_paper_to_markdown(
            sample_paper_dict, output_file=temp_output_file, add_yaml_frontmatter=True
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "---" in content
        assert 'title: "offshore-wind-farm-risk-assessment"' in content

    def test_no_yaml_frontmatter(self, temp_output_file, sample_paper_dict):
        """Test that YAML frontmatter can be disabled."""
        filepath = write_paper_to_markdown(
            sample_paper_dict, output_file=temp_output_file, add_yaml_frontmatter=False
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Should not have YAML frontmatter (title: at start)
        assert 'title: "offshore-wind-farm-risk-assessment"' not in content
        # The file should start with the title header
        assert content.startswith("#")

    def test_highlighted_title(self, temp_output_file, sample_paper_dict):
        """Test that title contains highlighted keywords."""
        filepath = write_paper_to_markdown(
            sample_paper_dict, output_file=temp_output_file
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Title should have highlighted keywords
        assert (
            '<span class="kw-offshore">Offshore</span>' in content
            or '<span class="kw-offshore">offshore</span>' in content.lower()
        )
        assert (
            '<span class="kw-wind-farm">Wind Farm</span>' in content
            or '<span class="kw-wind-farm">wind farm</span>' in content.lower()
        )
        assert (
            '<span class="kw-risk">Risk</span>' in content
            or '<span class="kw-risk">risk</span>' in content.lower()
        )

    def test_highlighted_abstract(self, temp_output_file, sample_paper_dict):
        """Test that abstract contains highlighted keywords."""
        filepath = write_paper_to_markdown(
            sample_paper_dict, output_file=temp_output_file
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Find the abstract section and check for highlights
        abstract_start = content.find("## Abstract")
        assert abstract_start != -1

        # Check that keywords in abstract are highlighted
        assert (
            '<span class="kw-collision">collision</span>' in content
            or '<span class="kw-collision">Collision</span>' in content
        )
        assert '<span class="kw-offshore">' in content
        assert (
            '<span class="kw-wind-farm">' in content
            or '<span class="kw-wind-farm' in content
        )


# =============================================================================
# Tests for write_paper_into_markdown function
# =============================================================================


class TestWriteSeriesPapersIntoMarkdown:
    """Tests for the write_paper_into_markdown function."""

    def test_creates_multiple_files(self, temp_output_dir, sample_dataframe):
        """Test that multiple files are created from DataFrame."""
        created_files = write_series_papers_into_markdown(
            sample_dataframe, output_dir=temp_output_dir
        )

        assert len(created_files) == 3
        assert all(f.endswith(".md") for f in created_files)

    def test_skips_existing_files(self, temp_output_dir, sample_dataframe):
        """Test that existing files are skipped when overwrite=False."""
        # First create files
        write_series_papers_into_markdown(sample_dataframe, output_dir=temp_output_dir)

        # Try again with overwrite=False - should skip all
        created_files = write_series_papers_into_markdown(
            sample_dataframe, output_dir=temp_output_dir, overwrite=False
        )

        assert len(created_files) == 0

    def test_overwrites_existing_files(self, temp_output_dir, sample_dataframe):
        """Test that existing files are overwritten when overwrite=True."""
        # First create files
        write_series_papers_into_markdown(sample_dataframe, output_dir=temp_output_dir)

        # Try again with overwrite=True - should recreate all
        created_files = write_series_papers_into_markdown(
            sample_dataframe, output_dir=temp_output_dir, overwrite=True
        )

        assert len(created_files) == 3


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
