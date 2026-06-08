"""
Pytest tests for paper_review_tools.py module

Tests cover:
- sanitize_filename function
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
from pathlib import Path

# Add the src directory to the Python path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from slrrag.convertmarkdown.paper_review_tools import (
    MANUAL_REVIEW_FIELD,
    FIELD_GROUPS,
    sanitize_filename,
    format_field_value,
    get_field_group,
    highlight_keywords_in_text,
    write_paper_into_markdown,
    write_paper_to_markdown,
    update_paper_review_status,
    get_next_paper_file,
    get_previous_paper_file,
)


# =============================================================================
# Fixtures
# =============================================================================

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
# Tests for sanitize_filename function
# =============================================================================

class TestSanitizeFilename:
    """Tests for the sanitize_filename function."""
    
    def test_basic_title(self):
        """Test sanitization of a basic title."""
        result = sanitize_filename("Offshore Wind Farms")
        assert result == "Offshore_Wind_Farms"
    
    def test_special_characters(self):
        """Test that special characters are replaced."""
        result = sanitize_filename("Title/with:special*chars?")
        assert "/" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
    
    def test_em_dash_and_en_dash(self):
        """Test handling of dashes."""
        result = sanitize_filename("Title – with — dashes")
        assert "–" not in result
        assert "—" not in result
        assert "_" in result
    
    def test_smart_quotes(self):
        """Test handling of smart quotes."""
        # Use actual smart quote characters (Unicode left and right single quotation marks)
        result = sanitize_filename("Title with \u2018smart\u2019 quotes")
        assert "\u2018" not in result
        assert "\u2019" not in result
        assert "_" in result  # Should be replaced with underscores
    
    def test_multiple_spaces(self):
        """Test that multiple spaces are collapsed."""
        result = sanitize_filename("Title   with   multiple    spaces")
        assert "  " not in result
        assert "___" not in result
    
    def test_empty_title(self):
        """Test handling of empty title."""
        result = sanitize_filename("")
        assert result == "untitled"
    
    def test_none_title(self):
        """Test handling of None title."""
        result = sanitize_filename(None)
        assert result == "untitled"
    
    def test_leading_trailing_underscores(self):
        """Test that leading/trailing underscores are removed."""
        result = sanitize_filename("__Title__")
        assert not result.startswith("_")
        assert not result.endswith("_")
    
    def test_long_title(self):
        """Test that long titles are truncated."""
        long_title = "A" * 200
        result = sanitize_filename(long_title)
        assert len(result) <= 150
    
    def test_title_with_brackets(self):
        """Test handling of brackets."""
        result = sanitize_filename("Title (with) [brackets]")
        assert "(" not in result
        assert ")" not in result
        assert "[" not in result
        assert "]" not in result


# =============================================================================
# Tests for format_field_value function
# =============================================================================

class TestFormatFieldValue:
    """Tests for the format_field_value function."""
    
    def test_na_values(self):
        """Test formatting of NA/None/empty values."""
        assert format_field_value("any_field", None) == "N/A"
        assert format_field_value("any_field", "") == "N/A"
        assert format_field_value("any_field", pd.NA) == "N/A"
    
    def test_pdf_link(self):
        """Test formatting of PDF field with URL."""
        result = format_field_value("pdf", "https://example.com/paper.pdf")
        assert "[PDF]" in result
        assert "https://example.com/paper.pdf" in result
    
    def test_pdf_plain_text(self):
        """Test formatting of PDF field without URL."""
        result = format_field_value("pdf", "paper.pdf")
        assert result == "paper.pdf"
    
    def test_keywords_formatting(self):
        """Test formatting of keyword fields."""
        result = format_field_value("keywords_scopus", "offshore|wind farm|risk")
        assert "#offshore" in result
        assert "#wind_farm" in result
        assert "#risk" in result
    
    def test_topics_formatting(self):
        """Test formatting of topic fields."""
        result = format_field_value("topic_openalex", "Engineering|Energy|Safety")
        assert "Engineering, Energy, Safety" in result
    
    def test_boolean_checkmarks(self):
        """Test formatting of boolean fields."""
        assert format_field_value("in_scopus", True) == "✓"
        assert format_field_value("in_scopus", False) == "✗"
        assert format_field_value("is_found", True) == "✓"
        assert format_field_value("is_reference", False) == "✗"
    
    def test_manual_review_formatting(self):
        """Test formatting of manual review field."""
        assert "👍" in format_field_value(MANUAL_REVIEW_FIELD, "keep")
        assert "👎" in format_field_value(MANUAL_REVIEW_FIELD, "removed")
        assert "🤔" in format_field_value(MANUAL_REVIEW_FIELD, "not-sure")
        # None returns "N/A" due to the initial NA check in the function
        assert format_field_value(MANUAL_REVIEW_FIELD, None) == "N/A"
    
    def test_relevance_scopus_formatting(self):
        """Test formatting of Scopus relevance score."""
        result = format_field_value("relevance_order_scopus", "0.95")
        assert result == "0.95"
        
        result = format_field_value("relevance_order_scopus", "0.8")
        assert result == "0.80"
    
    def test_relevance_openalex_formatting(self):
        """Test formatting of OpenAlex relevance score."""
        result = format_field_value("relevance_openalex", "0.87654321")
        assert result == "0.8765"


# =============================================================================
# Tests for get_field_group function
# =============================================================================

class TestGetFieldGroup:
    """Tests for the get_field_group function."""
    
    def test_identifiers_group(self):
        """Test fields in Identifiers group."""
        assert get_field_group("title") == "Identifiers"
    
    def test_publication_info_group(self):
        """Test fields in Publication Info group."""
        assert get_field_group("year") == "Publication Info"
        assert get_field_group("type") == "Publication Info"
    
    def test_content_group(self):
        """Test fields in Content group."""
        assert get_field_group("abstract") == "Content"
    
    def test_scopus_group(self):
        """Test fields in Scopus group."""
        assert get_field_group("relevance_order_scopus") == "Scopus"
        assert get_field_group("in_scopus") == "Scopus"
    
    def test_unknown_field(self):
        """Test unknown field returns 'Other'."""
        assert get_field_group("unknown_field") == "Other"


# =============================================================================
# Tests for highlight_keywords_in_text function
# =============================================================================

class TestHighlightKeywordsInText:
    """Tests for the highlight_keywords_in_text function."""
    
    def test_empty_string(self):
        """Test highlighting empty string."""
        result = highlight_keywords_in_text("")
        assert result == ""
    
    def test_none_input(self):
        """Test highlighting None."""
        result = highlight_keywords_in_text(None)
        assert result is None or result == ""
    
    def test_no_keywords(self):
        """Test text with no keywords."""
        text = "This is just regular text with no special words."
        result = highlight_keywords_in_text(text)
        assert result == text
        assert "<span" not in result
    
    def test_single_keyword(self):
        """Test text with a single keyword."""
        text = "This mentions offshore in the text."
        result = highlight_keywords_in_text(text)
        assert '<span class="kw-offshore">offshore</span>' in result
    
    def test_multiple_keywords(self):
        """Test text with multiple keywords."""
        text = "offshore wind farm collision risk assessment"
        result = highlight_keywords_in_text(text)
        assert '<span class="kw-offshore">offshore</span>' in result
        assert '<span class="kw-wind-farm">wind farm</span>' in result
        assert '<span class="kw-collision">collision</span>' in result
        assert '<span class="kw-risk">risk</span>' in result
        assert '<span class="kw-assess">assessment</span>' in result
    
    def test_case_insensitive(self):
        """Test case-insensitive matching."""
        text = "OFFSHORE Wind Farm COLLISION"
        result = highlight_keywords_in_text(text)
        assert '<span class="kw-offshore">OFFSHORE</span>' in result
        assert '<span class="kw-wind-farm">Wind Farm</span>' in result
        assert '<span class="kw-collision">COLLISION</span>' in result
    
    def test_multiline_text(self):
        """Test multiline text."""
        text = "Line 1: offshore\nLine 2: wind farm"
        result = highlight_keywords_in_text(text)
        assert '<span class="kw-offshore">offshore</span>' in result
        assert '<span class="kw-wind-farm">wind farm</span>' in result
    
    def test_already_highlighted(self):
        """Test text with already highlighted keywords."""
        text = 'This has <span class="kw-offshore">offshore</span> already.'
        result = highlight_keywords_in_text(text)
        # Should not double-wrap
        assert '<span class="kw-offshore"><span class="kw-offshore">' not in result
        # Should still highlight other keywords
        text_with_new = text + " collision"
        result = highlight_keywords_in_text(text_with_new)
        assert '<span class="kw-collision">collision</span>' in result
    
    def test_partial_words_not_matched(self):
        """Test that partial words are not matched."""
        text = "This is offshoring and collisionless."
        result = highlight_keywords_in_text(text)
        # These should NOT be highlighted as they're not exact matches
        assert "offshoring" not in result or '<span class="kw-offshore">' not in result
    
    def test_multi_word_phrases(self):
        """Test multi-word phrase matching."""
        text = "navigation risk assessment is important"
        result = highlight_keywords_in_text(text)
        assert '<span class="kw-navigation-risk-assessment">navigation risk assessment</span>' in result
    
    def test_words_in_parentheses(self):
        """Test that words inside parentheses are properly highlighted."""
        text = "This mentions (offshore) and (wind farm) keywords."
        result = highlight_keywords_in_text(text)
        assert '<span class="kw-offshore">offshore</span>' in result
        assert '<span class="kw-wind-farm">wind farm</span>' in result
    
    def test_words_in_brackets(self):
        """Test that words inside square brackets are properly highlighted."""
        text = "This mentions [offshore] and [collision] keywords."
        result = highlight_keywords_in_text(text)
        assert '<span class="kw-offshore">offshore</span>' in result
        assert '<span class="kw-collision">collision</span>' in result
    
    def test_words_incurly_braces(self):
        """Test that words inside curly braces are properly highlighted."""
        text = "This mentions {offshore} and {risk} keywords."
        result = highlight_keywords_in_text(text)
        assert '<span class="kw-offshore">offshore</span>' in result
        assert '<span class="kw-risk">risk</span>' in result


# =============================================================================
# Tests for write_paper_to_markdown function
# =============================================================================

class TestWritePaperToMarkdown:
    """Tests for the write_paper_to_markdown function."""
    
    def test_creates_file(self, temp_output_dir, sample_paper_dict):
        """Test that a file is created."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir
        )
        assert os.path.exists(filepath)
        assert filepath.endswith(".md")
    
    def test_file_contains_title(self, temp_output_dir, sample_paper_dict):
        """Test that the file contains the title."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir
        )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Title is now highlighted, so check for the highlighted version
        assert "# <span class=\"kw-offshore\">Offshore</span>" in content
        assert "<span class=\"kw-wind-farm\">Wind Farm</span>" in content
        assert "<span class=\"kw-risk\">Risk</span>" in content
        assert "<span class=\"kw-assess\">Assessment</span>" in content
    
    def test_file_contains_abstract(self, temp_output_dir, sample_paper_dict):
        """Test that the file contains the abstract."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir
        )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "## Abstract" in content
        # Abstract is now highlighted, so check for highlighted keywords
        assert "<span class=\"kw-collision\">collision</span>" in content
        assert "<span class=\"kw-risk\">risks</span>" in content
        assert "<span class=\"kw-offshore\">offshore</span>" in content
        assert "<span class=\"kw-wind-farm\">wind farms</span>" in content
        assert "<span class=\"kw-assess\">assess</span>" in content
    
    def test_file_contains_doi(self, temp_output_dir, sample_paper_dict):
        """Test that the file contains the DOI in frontmatter."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir
        )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # DOI is now in frontmatter
        assert 'doi: "10.1234/abc"' in content
    
    def test_yaml_frontmatter(self, temp_output_dir, sample_paper_dict):
        """Test that YAML frontmatter is included."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir,
            add_yaml_frontmatter=True
        )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "---" in content
        assert 'title: "Offshore Wind Farm Risk Assessment"' in content
    
    def test_no_yaml_frontmatter(self, temp_output_dir, sample_paper_dict):
        """Test that YAML frontmatter can be disabled."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir,
            add_yaml_frontmatter=False
        )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should not have YAML frontmatter (title: at start)
        assert 'title: "Offshore Wind Farm Risk Assessment"' not in content
        # The file should start with the title header
        assert content.startswith("#")
    
    def test_highlighted_title(self, temp_output_dir, sample_paper_dict):
        """Test that title contains highlighted keywords."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir
        )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Title should have highlighted keywords
        assert '<span class="kw-offshore">Offshore</span>' in content or \
               '<span class="kw-offshore">offshore</span>' in content.lower()
        assert '<span class="kw-wind-farm">Wind Farm</span>' in content or \
               '<span class="kw-wind-farm">wind farm</span>' in content.lower()
        assert '<span class="kw-risk">Risk</span>' in content or \
               '<span class="kw-risk">risk</span>' in content.lower()
    
    def test_highlighted_abstract(self, temp_output_dir, sample_paper_dict):
        """Test that abstract contains highlighted keywords."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir
        )
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the abstract section and check for highlights
        abstract_start = content.find("## Abstract")
        assert abstract_start != -1
        
        # Check that keywords in abstract are highlighted
        assert '<span class="kw-collision">collision</span>' in content or \
               '<span class="kw-collision">Collision</span>' in content
        assert '<span class="kw-offshore">' in content
        assert '<span class="kw-wind-farm">' in content or '<span class="kw-wind-farm' in content


# =============================================================================
# Tests for write_paper_into_markdown function
# =============================================================================

class TestWritePaperIntoMarkdown:
    """Tests for the write_paper_into_markdown function."""
    
    def test_creates_multiple_files(self, temp_output_dir, sample_dataframe):
        """Test that multiple files are created from DataFrame."""
        created_files = write_paper_into_markdown(
            sample_dataframe,
            output_dir=temp_output_dir
        )
        
        assert len(created_files) == 3
        assert all(f.endswith(".md") for f in created_files)
    
    def test_skips_existing_files(self, temp_output_dir, sample_dataframe):
        """Test that existing files are skipped when overwrite=False."""
        # First create files
        write_paper_into_markdown(
            sample_dataframe,
            output_dir=temp_output_dir
        )
        
        # Try again with overwrite=False - should skip all
        created_files = write_paper_into_markdown(
            sample_dataframe,
            output_dir=temp_output_dir,
            overwrite=False
        )
        
        assert len(created_files) == 0
    
    def test_overwrites_existing_files(self, temp_output_dir, sample_dataframe):
        """Test that existing files are overwritten when overwrite=True."""
        # First create files
        write_paper_into_markdown(
            sample_dataframe,
            output_dir=temp_output_dir
        )
        
        # Try again with overwrite=True - should recreate all
        created_files = write_paper_into_markdown(
            sample_dataframe,
            output_dir=temp_output_dir,
            overwrite=True
        )
        
        assert len(created_files) == 3


# =============================================================================
# Tests for update_paper_review_status function
# =============================================================================

class TestUpdatePaperReviewStatus:
    """Tests for the update_paper_review_status function."""
    
    def test_updates_status_keep(self, temp_output_dir, sample_paper_dict):
        """Test updating status to keep."""
        # Create a file
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir
        )
        
        # Update status
        result = update_paper_review_status(filepath, "keep")
        assert result is True
        
        # Check file - status is now only in frontmatter
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "manual_review: keep" in content
    
    def test_updates_status_removed(self, temp_output_dir, sample_paper_dict):
        """Test updating status to removed."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir
        )
        
        result = update_paper_review_status(filepath, "removed")
        assert result is True
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "manual_review: removed" in content
    
    def test_updates_status_not_sure(self, temp_output_dir, sample_paper_dict):
        """Test updating status to not-sure."""
        filepath = write_paper_to_markdown(
            sample_paper_dict,
            output_dir=temp_output_dir
        )
        
        result = update_paper_review_status(filepath, "not-sure")
        assert result is True
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "manual_review: not-sure" in content
    
    def test_invalid_status(self):
        """Test that invalid status raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test")
            f.flush()
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                update_paper_review_status(temp_path, "invalid")
        finally:
            os.unlink(temp_path)


# =============================================================================
# Tests for navigation functions
# =============================================================================

class TestNavigationFunctions:
    """Tests for navigation functions."""
    
    def test_get_next_paper_file(self, temp_output_dir, sample_dataframe):
        """Test getting next paper file."""
        # Create files
        write_paper_into_markdown(
            sample_dataframe,
            output_dir=temp_output_dir
        )
        
        # Get list of files
        files = sorted([f for f in os.listdir(temp_output_dir) if f.endswith('.md')])
        
        # Test getting next file
        first_file = os.path.join(temp_output_dir, files[0])
        next_file = get_next_paper_file(first_file, temp_output_dir)
        
        assert next_file is not None
        assert next_file == os.path.join(temp_output_dir, files[1])
    
    def test_get_previous_paper_file(self, temp_output_dir, sample_dataframe):
        """Test getting previous paper file."""
        # Create files
        write_paper_into_markdown(
            sample_dataframe,
            output_dir=temp_output_dir
        )
        
        # Get list of files
        files = sorted([f for f in os.listdir(temp_output_dir) if f.endswith('.md')])
        
        # Test getting previous file
        second_file = os.path.join(temp_output_dir, files[1])
        prev_file = get_previous_paper_file(second_file, temp_output_dir)
        
        assert prev_file is not None
        assert prev_file == os.path.join(temp_output_dir, files[0])
    
    def test_get_next_at_end(self, temp_output_dir, sample_dataframe):
        """Test getting next file at the end of list."""
        # Create files
        write_paper_into_markdown(
            sample_dataframe,
            output_dir=temp_output_dir
        )
        
        # Get list of files
        files = sorted([f for f in os.listdir(temp_output_dir) if f.endswith('.md')])
        
        # Test getting next file from last file
        last_file = os.path.join(temp_output_dir, files[-1])
        next_file = get_next_paper_file(last_file, temp_output_dir)
        
        assert next_file is None
    
    def test_get_previous_at_beginning(self, temp_output_dir, sample_dataframe):
        """Test getting previous file at the beginning of list."""
        # Create files
        write_paper_into_markdown(
            sample_dataframe,
            output_dir=temp_output_dir
        )
        
        # Get list of files
        files = sorted([f for f in os.listdir(temp_output_dir) if f.endswith('.md')])
        
        # Test getting previous file from first file
        first_file = os.path.join(temp_output_dir, files[0])
        prev_file = get_previous_paper_file(first_file, temp_output_dir)
        
        assert prev_file is None


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
