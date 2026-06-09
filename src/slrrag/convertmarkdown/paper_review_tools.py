"""
Paper Review Tools for Obsidian

This script converts a pandas DataFrame of papers into individual markdown files
optimized for review in Obsidian with the Paper Review theme.

Each markdown file represents one paper with all its metadata fields.
The files include a manual_review field that can be set to "keep", "removed", or "not-sure"
using Obsidian hotkeys.
"""

import pandas as pd
import os
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm

# Import the keyword highlighting functionality
from slrrag.convertmarkdown.highlight_keywords import highlight_keywords_in_text


# Configuration
MANUAL_REVIEW_FIELD = "manual_review"
DEFAULT_REVIEW_STATUS = None  # Can be "keep", "removed", "not-sure", or None

# Field groupings for better organization in markdown


def slugify(title: str, limit: int = None) -> str:
    """
    Convert a paper title to a URL-friendly slug.

    Args:
        title: The paper title

    Returns:
        A slugified version of the title (lowercase, hyphens instead of spaces, special chars removed)
    """
    if pd.isna(title) or title is None:
        return "untitled"

    # Convert to string, lowercase, and strip
    slug = str(title).strip().lower()

    # Replace spaces with hyphens
    slug = slug.replace(" ", "-")

    # Remove special characters and replace with empty or hyphen
    # Characters to remove completely
    for char in [
        "/",
        "\\",
        ":",
        "*",
        "?",
        '"',
        "<",
        ">",
        "|",
        "–",
        "—",
        "‘",
        "’",
        ",",
        ";",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
    ]:
        slug = slug.replace(char, "")

    # Replace multiple hyphens with single hyphen
    while "--" in slug:
        slug = slug.replace("--", "-")

    # Remove trailing/leading hyphens
    slug = slug.rstrip("-").lstrip("-")

    # Limit length
    if limit is not None:
        slug = slug[:limit]

    # If empty after all processing, return untitled
    if not slug:
        return "untitled"

    return slug


def write_paper_to_markdown(
    paper: Dict[str, Any],
    output_file: Path,
    add_yaml_frontmatter: bool = True,
) -> str:
    """
    Write a single paper to a markdown file.

    Args:
        paper: Dictionary containing paper data
        output_file: Directory to save the markdown file
        add_yaml_frontmatter: Whether to add YAML frontmatter

    Returns:
        Path to the created markdown file
    """
    # Get title and create filename
    title = paper.get("title", "Untitled")

    # Ensure manual_review field exists
    if MANUAL_REVIEW_FIELD not in paper:
        paper[MANUAL_REVIEW_FIELD] = DEFAULT_REVIEW_STATUS

    # Start building markdown content
    lines = []

    # Add YAML frontmatter with metadata
    if add_yaml_frontmatter:
        lines.append("---")
        lines.append(f'title: "{slugify(title)}"')

        # Add DOI
        doi = paper.get("doi", "")
        if doi and doi != "N/A" and str(doi).lower() not in ["nan", "none", ""]:
            lines.append(f'doi: "{doi}"')

        # Add tags field (placeholder)
        lines.append("tags:")

        # Add PDF link
        pdf = paper.get("pdf", "")
        if pdf and pdf != "N/A":
            lines.append(f'pdf: "{pdf}"')

        # Add date of publication
        date = paper.get("date", "")
        if date and date != "N/A":
            lines.append(f'date: "{date}"')

        # Add database IDs
        for db in ["scopus", "openalex", "lens", "dimensions"]:
            id_field = f"id_{db}"
            id_value = paper.get(id_field, "")
            if id_value and id_value != "N/A":
                lines.append(f'{id_field}: "{id_value}"')

        # Add manual review status
        review_status = paper.get(MANUAL_REVIEW_FIELD)
        if review_status and review_status != "None" and not pd.isna(review_status):
            lines.append(f"manual_review: {review_status}")

        lines.append("---")
        lines.append("")

    # Add title with keyword highlighting
    highlighted_title = highlight_keywords_in_text(title)
    lines.append(f"# {highlighted_title}")
    lines.append("")

    # Add abstract (most important field)
    abstract = paper.get("abstract", "")
    if not pd.isna(abstract) and abstract != "N/A":
        lines.append("## Abstract")
        lines.append("")
        highlighted_abstract = highlight_keywords_in_text(abstract)
        lines.append(highlighted_abstract)
        lines.append("")

    # Collect topics from all database fields
    for prefix in ["topic", "keywords", "fields", "relevance_order", "relevance"]:
        lines.append(f"## {prefix}")
        for db in ["scopus", "openalex", "lens", "dimensions"]:
            prefix_db = f"{prefix}_{db}"
            if prefix_db in paper:
                topics = paper.get(prefix_db, "")
                if not pd.isna(topics) and topics != "N/A" and isinstance(topics, str):
                    lines.append("**" + db + "**: " + topics)

    # Write to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_file


def write_series_papers_into_markdown(
    df: pd.DataFrame,
    output_dir: str = "./papers",
    add_yaml_frontmatter: bool = True,
    overwrite: bool = False,
    batch_size: int = 50,
) -> List[str]:
    """
    Convert a pandas DataFrame of papers to individual markdown files.
    Files are split into batches of `batch_size` (default 50) in numerically prefixed subfolders.

    This is the main function that processes the entire DataFrame.

    Args:
        df: pandas DataFrame containing paper data with columns as described
        output_dir: Directory to save markdown files (default: ./papers)
        add_yaml_frontmatter: Whether to add YAML frontmatter (default: True)
        overwrite: Whether to overwrite existing files (default: False)
        batch_size: Number of papers per batch folder (default: 50)

    Returns:
        List of paths to created markdown files

    Example:
        >>> import pandas as pd
        >>> df = pd.read_csv("papers.csv")
        >>> created_files = write_paper_into_markdown(df, output_dir="./my_papers", batch_size=50)
        >>> print(f"Created {len(created_files)} markdown files")
    """
    created_files = []

    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Calculate number of batches needed
    total_papers = len(df)
    num_batches = (total_papers + batch_size - 1) // batch_size

    # Iterate through each batch
    for batch_num in tqdm(range(num_batches), desc="Processing batches", unit="batch"):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_papers)
        batch_df = df.iloc[start_idx:end_idx]

        # Create batch subfolder with numerical prefix
        batch_dir = os.path.join(output_dir, f"{batch_num + 1:03d}_batch")
        Path(batch_dir).mkdir(parents=True, exist_ok=True)

        # Iterate through each row (paper) in the batch DataFrame
        for idx, row in tqdm(
            batch_df.iterrows(),
            desc=f"Batch {batch_num + 1}",
            unit="paper",
            leave=False,
        ):
            paper_dict = row.to_dict()

            # Create filename from title
            title = paper_dict.get("title", f"paper_{idx}")
            slug = slugify(title, limit=100)
            filename = slug + ".md"
            filepath = os.path.join(batch_dir, filename)

            # Check if file exists and overwrite is False
            if not overwrite and os.path.exists(filepath):
                continue

            # Write the paper
            created_path = write_paper_to_markdown(
                paper_dict,
                output_file=filepath,
                add_yaml_frontmatter=add_yaml_frontmatter,
            )
            created_files.append(created_path)

    print(f"\nTotal files created: {len(created_files)} in {num_batches} batch folders")
    return created_files


# Example usage
if __name__ == "__main__":
    # Example: Load CSV and create markdown files
    import sys

    if len(sys.argv) < 2:
        print("Usage: python paper_review_tools.py <input_csv> [output_dir]")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./papers"

    # Read the CSV
    df = pd.read_csv(input_csv).head(150)

    # Create markdown files
    print(f"Processing {len(df)} papers from {input_csv}...")
    created_files = write_series_papers_into_markdown(df, output_dir=output_dir)

    print(f"\nDone! Created {len(created_files)} markdown files in {output_dir}")
