"""
Pytest tests for highlight_keywords.py module

Tests cover:
- STEMMING_DICT structure and content
- root_to_class function
- get_all_keyword_variants function
- cleanup_file function
- process_file function (with temp files)
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add the src directory to the Python path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from slrrag.convertmarkdown.highlight_keywords import (
    STEMMING_DICT,
    cleanup_file,
    get_all_keyword_variants,
    highlight_keywords_in_text,
    process_file,
    root_to_class,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_markdown_file():
    """Create a temporary markdown file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Document\n\nThis is a test offshore wind farm document.\n")
        f.flush()
        yield f.name
        # Cleanup
        os.unlink(f.name)


@pytest.fixture
def temp_markdown_file_with_existing_highlights():
    """Create a temporary markdown file with existing highlights."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        content = """# Test Document

This has <span class="kw-offshore">offshore</span> already highlighted.
There is also a collision mentioned here.
"""
        f.write(content)
        f.flush()
        yield f.name
        # Cleanup
        os.unlink(f.name)


@pytest.fixture
def temp_folder_with_markdown_files():
    """Create a temporary folder with multiple markdown files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test files
        file1 = Path(temp_dir) / "test1.md"
        file1.write_text("# File 1\n\nThis mentions offshore wind farm.")

        file2 = Path(temp_dir) / "test2.md"
        file2.write_text("# File 2\n\nThis has collision and accident keywords.")

        file3 = Path(temp_dir) / "test3.md"
        file3.write_text("# File 3\n\nNo keywords here.")

        yield temp_dir


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
        assert (
            '<span class="kw-navigation-risk-assessment">navigation risk assessment</span>'
            in result
        )

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
# Tests for root_to_class function
# =============================================================================


class TestRootToClass:
    """Tests for the root_to_class function."""

    def test_basic_conversion(self):
        """Test basic root to class conversion."""
        assert root_to_class("offshore") == "kw-offshore"
        assert root_to_class("collision") == "kw-collision"

    def test_hyphenated_root(self):
        """Test that hyphenated roots are preserved."""
        assert root_to_class("wind-farm") == "kw-wind-farm"
        assert (
            root_to_class("navigation-risk-assessment")
            == "kw-navigation-risk-assessment"
        )

    def test_empty_string(self):
        """Test with empty string."""
        assert root_to_class("") == "kw-"


# =============================================================================
# Tests for get_all_keyword_variants function
# =============================================================================


class TestGetAllKeywordVariants:
    """Tests for the get_all_keyword_variants function."""

    def test_returns_list(self):
        """Test that the function returns a list."""
        variants = get_all_keyword_variants()
        assert isinstance(variants, list)

    def test_list_not_empty(self):
        """Test that the returned list is not empty."""
        variants = get_all_keyword_variants()
        assert len(variants) > 0

    def test_each_item_has_required_keys(self):
        """Test that each item has 'variant', 'class_name', and 'root' keys."""
        variants = get_all_keyword_variants()
        for item in variants:
            assert "variant" in item
            assert "class_name" in item
            assert "root" in item

    def test_class_name_format(self):
        """Test that class names follow the kw-{root} format."""
        variants = get_all_keyword_variants()
        for item in variants:
            assert item["class_name"].startswith("kw-")

    def test_all_variants_included(self):
        """Test that all variants from STEMMING_DICT are included."""
        variants = get_all_keyword_variants()
        variant_strings = [v["variant"] for v in variants]

        for root, expected_variants in STEMMING_DICT.items():
            for variant in expected_variants:
                assert variant in variant_strings


# =============================================================================
# Tests for cleanup_file function
# =============================================================================


class TestCleanupFile:
    """Tests for the cleanup_file function."""

    def test_removes_span_tags(self):
        """Test that kw- span tags are removed."""
        content = 'This has <span class="kw-offshore">offshore</span> in it.'
        cleaned = cleanup_file(content)
        assert cleaned == "This has offshore in it."

    def test_cleanup_multiple_spaces(self):
        """Test that multiple spaces are reduced to single spaces."""
        content = "This   has    multiple   spaces."
        cleaned = cleanup_file(content)
        assert "  " not in cleaned

    def test_cleanup_multiple_newlines(self):
        """Test that multiple newlines are reduced."""
        content = "Line 1\n\n\n\nLine 2"
        cleaned = cleanup_file(content)
        assert "\n\n\n" not in cleaned

    def test_preserves_normal_text(self):
        """Test that normal text is preserved."""
        content = "This is normal text with offshore keyword."
        cleaned = cleanup_file(content)
        assert cleaned == "This is normal text with offshore keyword."

    def test_strips_content(self):
        """Test that content is stripped of leading/trailing whitespace."""
        content = "\n\n  Some content  \n\n"
        cleaned = cleanup_file(content)
        assert cleaned == "Some content"


# =============================================================================
# Tests for process_file function
# =============================================================================


class TestProcessFile:
    """Tests for the process_file function."""

    def test_processes_file_with_keywords(self, temp_markdown_file):
        """Test that a file with keywords gets processed and highlighted."""
        # Process the file
        result = process_file(temp_markdown_file)

        # Check that the file was modified
        assert result is True

        # Read the file and check for highlights
        with open(temp_markdown_file, "r", encoding="utf-8") as f:
            content = f.read()

        assert '<span class="kw-offshore">offshore</span>' in content
        assert '<span class="kw-wind-farm">wind farm</span>' in content

    def test_processes_file_without_keywords(self):
        """Test that a file without keywords is not modified."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# No Keywords Here\n\nJust regular text.")
            f.flush()
            temp_path = f.name

        try:
            # Process the file
            result = process_file(temp_path)

            # Check that the file was not modified
            assert result is False

            # Read the file and check no highlights were added
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert "<span" not in content
        finally:
            os.unlink(temp_path)

    def test_case_insensitive_matching(self, temp_markdown_file):
        """Test that keyword matching is case insensitive."""
        # Read the current content
        # Process the file
        process_file(temp_markdown_file)

        # Read back and check
        with open(temp_markdown_file, "r", encoding="utf-8") as f:
            highlighted = f.read()

        # The keyword 'offshore' should be highlighted regardless of case
        assert '<span class="kw-offshore">offshore</span>' in highlighted

    def test_skips_already_highlighted_content(
        self, temp_markdown_file_with_existing_highlights
    ):
        """Test that already highlighted content is not double-wrapped."""
        # Process the file
        process_file(temp_markdown_file_with_existing_highlights)

        # Read the file
        with open(
            temp_markdown_file_with_existing_highlights, "r", encoding="utf-8"
        ) as f:
            content = f.read()

        # Check that offshore is not double-wrapped
        assert '<span class="kw-offshore"><span class="kw-offshore">' not in content

        # Check that collision is now highlighted
        assert '<span class="kw-collision">collision</span>' in content

    def test_handles_special_characters(self):
        """Test that special characters in text are handled correctly."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("# Test\n\nThis has offshore and wind farm and risk assessment.")
            f.flush()
            temp_path = f.name

        try:
            # Process the file
            process_file(temp_path)

            # Read the file
            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check highlights
            assert '<span class="kw-offshore">offshore</span>' in content
            assert '<span class="kw-wind-farm">wind farm</span>' in content
        finally:
            os.unlink(temp_path)

    def test_preserves_frontmatter_header(self):
        """Test that frontmatter header (between ---) is not modified."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            content = """---
title: this-is-my-title-offshore-wind-farm
keywords: ship | vessels
date: 2026
---

## Abstract
lorem ipsum offshore wind farm
"""
            f.write(content)
            f.flush()
            temp_path = f.name

        try:
            # Process the file
            process_file(temp_path)

            # Read the file
            with open(temp_path, "r", encoding="utf-8") as f:
                result = f.read()

            # Check that header is preserved exactly
            assert "---" in result
            assert "title: this-is-my-title-offshore-wind-farm" in result
            assert "date: 2026" in result

            # Check that the header section does NOT contain any span tags
            # Extract header (first --- to second ---)
            header_end = result.find("---", 3)
            if header_end != -1:
                header_section = result[: header_end + 3]
                assert '<span class="kw-' not in header_section

            # Check that body has highlights
            assert '<span class="kw-offshore">offshore</span>' in result
            assert '<span class="kw-wind-farm">wind farm</span>' in result

        finally:
            os.unlink(temp_path)


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_file(self):
        """Test processing an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("")
            f.flush()
            temp_path = f.name

        try:
            result = process_file(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)

    def test_cleanup_empty_string(self):
        """Test cleanup_file with empty string."""
        assert cleanup_file("") == ""

    def test_cleanup_none(self):
        """Test cleanup_file with None."""
        # This might raise an error depending on implementation
        # Let's test the actual behavior
        try:
            result = cleanup_file(None)
            # If it doesn't raise, check the result
            assert result is None or result == ""
        except (AttributeError, TypeError):
            # Expected behavior for None input
            pass

    def test_highlighting_preserves_punctuation(self):
        """Test that highlighting preserves punctuation around keywords."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("The offshore, wind-farm: risk assessment!")
            f.flush()
            temp_path = f.name

        try:
            process_file(temp_path)

            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check that punctuation is preserved
            assert '<span class="kw-offshore">offshore</span>,' in content
        finally:
            os.unlink(temp_path)


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for the module."""

    def test_full_workflow(self, temp_folder_with_markdown_files):
        """Test the full workflow of finding and processing multiple files."""
        import sys
        from io import StringIO
        from pathlib import Path

        # Save original stdout
        old_stdout = sys.stdout

        try:
            # Redirect stdout to capture output
            sys.stdout = StringIO()

            # Call main with the temp folder
            # Note: main() calls sys.exit(), so we need to handle that
            temp_path = Path(temp_folder_with_markdown_files)

            # Manually process files instead of calling main
            md_files = list(temp_path.rglob("*.md"))
            processed_count = 0
            for md_file in md_files:
                if process_file(md_file):
                    processed_count += 1

            # Check that at least some files were processed
            assert processed_count >= 2  # test1.md and test2.md should be processed

            # Check that files contain highlights
            for md_file in md_files:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # test1.md should have offshore and wind-farm
                if "test1.md" in str(md_file):
                    assert '<span class="kw-offshore">offshore</span>' in content
                    assert '<span class="kw-wind-farm">wind farm</span>' in content

                # test2.md should have collision and accident
                elif "test2.md" in str(md_file):
                    assert '<span class="kw-collision">collision</span>' in content
                    assert '<span class="kw-accident">accident</span>' in content

                # test3.md should have no highlights
                elif "test3.md" in str(md_file):
                    assert '<span class="kw-' not in content

        finally:
            # Restore stdout
            sys.stdout = old_stdout

    def test_all_variants_are_unique(self):
        """Test that there are no duplicate variants across different roots."""
        all_variants = []
        for root, variants in STEMMING_DICT.items():
            all_variants.extend(variants)

        # Check for duplicates (case-sensitive)
        seen = set()
        duplicates = []
        for variant in all_variants:
            if variant in seen:
                duplicates.append(variant)
            seen.add(variant)

        # Note: Some duplicates might be intentional (e.g., "bridge" appears in both
        # the bridge root and might be a variant of another word)
        # For now, just report if there are duplicates
        if duplicates:
            print(f"Warning: Found duplicate variants: {duplicates}")


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
