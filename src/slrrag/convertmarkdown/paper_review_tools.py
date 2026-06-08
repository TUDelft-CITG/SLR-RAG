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
import regex as re
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import the keyword highlighting functionality
from slrrag.convertmarkdown.highlight_keywords import STEMMING_DICT, root_to_class, get_all_keyword_variants


# Configuration
MANUAL_REVIEW_FIELD = "manual_review"
DEFAULT_REVIEW_STATUS = None  # Can be "keep", "removed", "not-sure", or None

# Field groupings for better organization in markdown
FIELD_GROUPS = {
    "Identifiers": ["title"],
    "Publication Info": ["type", "year"],
    "Content": ["abstract"],
    "Scopus": ["relevance_order_scopus", "in_scopus"],
    "OpenAlex": ["relevance_openalex", "in_openalex"],
    "Lens": ["in_lens"],
    "Dimensions": ["in_dimensions"],
    "Status": ["is_found", "is_reference", MANUAL_REVIEW_FIELD],
}


def sanitize_filename(title: str) -> str:
    """
    Convert a paper title to a safe filename.
    
    Args:
        title: The paper title
        
    Returns:
        A sanitized filename with special characters removed
    """
    if not title or pd.isna(title):
        return "untitled"
    
    # Convert to string and strip
    filename = str(title).strip()
    
    # Replace problematic characters with underscores or remove them
    # Characters to replace with underscore
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '–', '—', '‘', '’', ',', ';', '(' , ')', '[', ']', '{', '}']:
        filename = filename.replace(char, '_')
    
    # Replace multiple spaces with single space first
    while '  ' in filename:
        filename = filename.replace('  ', ' ')
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Replace multiple underscores with single underscore
    while '__' in filename:
        filename = filename.replace('__', '_')
    
    # Limit length to 150 characters
    filename = filename[:150]
    
    # Remove trailing underscores
    filename = filename.rstrip('_')
    
    # Remove leading underscores
    filename = filename.lstrip('_')
    
    # If empty after all processing, return untitled
    if not filename:
        return "untitled"
    
    return filename


def slugify(title: str) -> str:
    """
    Convert a paper title to a URL-friendly slug.

    Args:
        title: The paper title
        
    Returns:
        A slugified version of the title (lowercase, hyphens instead of spaces, special chars removed)
    """
    if not title or pd.isna(title):
        return "untitled"
    
    # Convert to string, lowercase, and strip
    slug = str(title).strip().lower()
    
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    
    # Remove special characters and replace with empty or hyphen
    # Characters to remove completely
    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '–', '—', '‘', '’', ',', ';', '(', ')', '[', ']', '{', '}']:
        slug = slug.replace(char, '')
    
    # Replace multiple hyphens with single hyphen
    while '--' in slug:
        slug = slug.replace('--', '-')
    
    # Remove trailing/leading hyphens
    slug = slug.rstrip('-').lstrip('-')
    
    # Limit length to 150 characters
    slug = slug[:150]
    
    # If empty after all processing, return untitled
    if not slug:
        return "untitled"
    
    return slug


def format_field_value(field_name: str, value: Any) -> str:
    """
    Format a field value for markdown display.
    
    Args:
        field_name: Name of the field
        value: The value to format
        
    Returns:
        Formatted string representation
    """
    if pd.isna(value) or value is None or value == '':
        return "N/A"
    
    # Special formatting for certain fields
    if field_name == "pdf":
        if isinstance(value, str) and value.startswith('http'):
            return f"[PDF]({value})"
        return str(value)
    
    if field_name in ["keywords_scopus", "keywords_openalex", "keywords_lens", "keywords_dimensions"]:
        if isinstance(value, str):
            # Format pipe-separated keywords as tags
            keywords = [k.strip() for k in value.split('|') if k.strip()]
            if keywords:
                return ", ".join(f"#{k.replace(' ', '_')}" for k in keywords)
        return str(value)
    
    if field_name in ["topic_openalex", "topic_lens", "topic_dimensions", "fields_openalex"]:
        if isinstance(value, str):
            topics = [t.strip() for t in value.split('|') if t.strip()]
            if topics:
                return ", ".join(topics)
        return str(value)
    
    if field_name in ["in_scopus", "in_openalex", "in_lens", "in_dimensions", "is_found", "is_reference"]:
        return "✓" if value else "✗"
    
    if field_name == MANUAL_REVIEW_FIELD:
        if value == "keep":
            return "👍 **Keep**"
        elif value == "removed":
            return "👎 **Removed**"
        elif value == "not-sure":
            return "🤔 **Not Sure**"
        return "❓ Not Reviewed"
    
    if field_name == "relevance_order_scopus":
        try:
            return f"{float(value):.2f}"
        except (ValueError, TypeError):
            return str(value)
    
    if field_name == "relevance_openalex":
        try:
            return f"{float(value):.4f}"
        except (ValueError, TypeError):
            return str(value)
    
    return str(value)


def get_field_group(field_name: str) -> str:
    """
    Get the group name for a field.
    
    Args:
        field_name: Name of the field
        
    Returns:
        Group name or "Other" if not found
    """
    for group_name, fields in FIELD_GROUPS.items():
        if field_name in fields:
            return group_name
    return "Other"


def highlight_keywords_in_text(text: str) -> str:
    """
    Apply keyword highlighting to a text string using the STEMMING_DICT.
    Only highlights whole words that are not already inside kw- spans.
    
    Args:
        text: The text to highlight
        
    Returns:
        The text with keywords wrapped in appropriate kw- class spans
    """
    if not text or not isinstance(text, str):
        return text
    
    all_variants = get_all_keyword_variants()
    
    # Sort by length (longest first) to avoid partial matches
    all_variants.sort(key=lambda x: len(x['variant']), reverse=True)
    
    for item in all_variants:
        variant = item['variant']
        class_name = item['class_name']
        
        # Regex pattern: match whole word NOT already inside a kw- span
        pattern = r'(?<!class="kw-[^"]*">[^<]*\b)(\b' + re.escape(variant) + r'\b)(?![^<]*</span>)'
        
        new_text = re.sub(
            pattern,
            rf'<span class="{class_name}">\1</span>',
            text,
            flags=re.IGNORECASE
        )
        
        if new_text != text:
            text = new_text
    
    return text


def write_paper_to_markdown(
    paper: Dict[str, Any],
    output_dir: str,
    template_path: Optional[str] = None,
    add_yaml_frontmatter: bool = True
) -> str:
    """
    Write a single paper to a markdown file.
    
    Args:
        paper: Dictionary containing paper data
        output_dir: Directory to save the markdown file
        template_path: Optional path to a custom template file
        add_yaml_frontmatter: Whether to add YAML frontmatter
        
    Returns:
        Path to the created markdown file
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Get title and create filename
    title = paper.get("title", "Untitled")
    slug = slugify(title)
    filename = slug + ".md"
    filepath = os.path.join(output_dir, filename)
    
    # Ensure manual_review field exists
    if MANUAL_REVIEW_FIELD not in paper:
        paper[MANUAL_REVIEW_FIELD] = DEFAULT_REVIEW_STATUS
    
    # Start building markdown content
    lines = []
    
    # Add YAML frontmatter with metadata
    if add_yaml_frontmatter:
        lines.append("---")
        lines.append(f"title: \"{slug}\"")
        
        # Add DOI
        doi = paper.get("doi", "")
        if doi and doi != "N/A" and str(doi).lower() not in ['nan', 'none', '']:
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
    
    # Collect topics from all database fields
    db_topics = {}
    db_keywords = {}

    for db in ["scopus", "openalex", "lens", "dimensions"]:
        db_topics[db] = []
        db_keywords[db] = []

    for db in ["scopus", "openalex", "lens", "dimensions"]:
        topics_field = f"topic_{db}"
        if topics_field in paper:
            topics = paper.get(topics_field, "")
            if topics and topics != "N/A" and isinstance(topics, str):
                topic_list = [t.strip() for t in topics.split('|') if t.strip()]
                db_topics[db].extend(topic_list)
        
        keywords_field = f"keywords_{db}"
        if keywords_field in paper:
            keywords = paper.get(keywords_field, "")
            if keywords and keywords != "N/A" and isinstance(keywords, str):
                kw_list = [k.strip() for k in keywords.split('|') if k.strip()]
                db_keywords[db].extend(kw_list)

    # Add topics (Openalex, Lens, Dimensions) - skip Scopus as per requirement
    topics_has_content = False
    for db in ["openalex", "lens", "dimensions"]:
        if db_topics[db]:
            topics_has_content = True
            break
    
    if topics_has_content:
        for db in ["openalex", "lens", "dimensions"]:
            if db_topics[db]:
                lines.append(f"**Topic {db.capitalize()}** : {', '.join(db_topics[db])}")
        lines.append("")
    
    # Add abstract (most important field)
    abstract = paper.get("abstract", "")
    if not pd.isna(abstract) and abstract != "N/A":
        lines.append("## Abstract")
        lines.append("")
        highlighted_abstract = highlight_keywords_in_text(abstract)
        lines.append(highlighted_abstract)
        lines.append("")

    # Add keywords from all databases
    keywords_has_content = False
    for db in ["scopus", "openalex", "lens", "dimensions"]:
        if db_keywords[db]:
            keywords_has_content = True
            break
    
    if keywords_has_content:
        lines.append("## Keywords")
        lines.append("")
        for db in ["scopus", "openalex", "lens", "dimensions"]:
            if db_keywords[db]:
                keywords_as_tags = [f"#{kw.replace(' ', '_')}" for kw in db_keywords[db]]
                lines.append(f"**{db.capitalize()}** : {', '.join(keywords_as_tags)}")
        lines.append("")
    
    # Group remaining fields by category
    lines.append("---")
    lines.append("")
    lines.append("## Metadata")
    lines.append("")
    
    # Process fields in groups - exclude fields already in frontmatter
    excluded_fields = {"title", "abstract", "pdf", "doi", "date", "manual_review_field", 
                      "id_scopus", "id_openalex", "id_lens", "id_dimensions",
                      "keywords_scopus", "keywords_openalex", "keywords_lens", "keywords_dimensions",
                      "topic_scopus", "topic_openalex", "topic_lens", "topic_dimensions",
                      "fields_openalex"}
    
    for group_name, fields in FIELD_GROUPS.items():
        group_fields = [f for f in fields if f in paper and f not in excluded_fields]
        if group_fields:
            lines.append(f"### {group_name}")
            lines.append("")
            for field in sorted(group_fields):
                value = paper[field]
                formatted_value = format_field_value(field, value)
                field_display = field.replace("_", " ").title()
                lines.append(f"- **{field_display}:** {formatted_value}")
            lines.append("")
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    return filepath


def write_paper_into_markdown(
    df: pd.DataFrame,
    output_dir: str = "./papers",
    template_path: Optional[str] = None,
    add_yaml_frontmatter: bool = True,
    overwrite: bool = False
) -> List[str]:
    """
    Convert a pandas DataFrame of papers to individual markdown files.
    
    This is the main function that processes the entire DataFrame.
    
    Args:
        df: pandas DataFrame containing paper data with columns as described
        output_dir: Directory to save markdown files (default: ./papers)
        template_path: Optional path to a custom template file
        add_yaml_frontmatter: Whether to add YAML frontmatter (default: True)
        overwrite: Whether to overwrite existing files (default: False)
        
    Returns:
        List of paths to created markdown files
        
    Example:
        >>> import pandas as pd
        >>> df = pd.read_csv("papers.csv")
        >>> created_files = write_paper_into_markdown(df, output_dir="./my_papers")
        >>> print(f"Created {len(created_files)} markdown files")
    """
    created_files = []
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Iterate through each row (paper) in the DataFrame
    for idx, row in df.iterrows():
        paper_dict = row.to_dict()
        
        # Create filename from title
        title = paper_dict.get("title", f"paper_{idx}")
        slug = slugify(title)
        filename = slug + ".md"
        filepath = os.path.join(output_dir, filename)
        
        # Check if file exists and overwrite is False
        if not overwrite and os.path.exists(filepath):
            print(f"Skipping existing file: {filename}")
            continue
        
        # Write the paper
        created_path = write_paper_to_markdown(
            paper_dict,
            output_dir=output_dir,
            template_path=template_path,
            add_yaml_frontmatter=add_yaml_frontmatter
        )
        created_files.append(created_path)
        print(f"Created: {filename}")
    
    print(f"\nTotal files created: {len(created_files)}")
    return created_files


def update_paper_review_status(
    markdown_file: str,
    status: str
) -> bool:
    """
    Update the manual_review status in a markdown file.
    
    This function can be called programmatically to update the classification.
    
    Args:
        markdown_file: Path to the markdown file
        status: One of "keep", "removed", "not-sure", or None
        
    Returns:
        True if update was successful, False otherwise
    """
    if status not in ["keep", "removed", "not-sure", None]:
        raise ValueError(f"Invalid status: {status}. Must be 'keep', 'removed', 'not-sure', or None")
    
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update YAML frontmatter
        if "---" in content:
            lines = content.split('\n')
            new_lines = []
            in_frontmatter = False
            updated = False
            
            for line in lines:
                if line.strip() == "---":
                    if in_frontmatter:
                        # Closing frontmatter
                        in_frontmatter = False
                    else:
                        # Opening frontmatter
                        in_frontmatter = True
                        new_lines.append(line)
                        continue
                
                if in_frontmatter:
                    if line.strip().startswith("manual_review:"):
                        if status is None:
                            new_lines.append(f"manual_review: ")
                        else:
                            new_lines.append(f"manual_review: {status}")
                        updated = True
                    else:
                        new_lines.append(line)
                else:
                    new_lines.append(line)
            
            if not updated:
                # Add manual_review field
                for i, line in enumerate(new_lines):
                    if line.strip() == "---" and i > 0:
                        new_lines.insert(i, f"manual_review: {status if status else ''}")
                        break
            
            content = '\n'.join(new_lines)
        
        # Update the status badge in the content
        if status == "keep":
            content = content.replace("⚪ NOT REVIEWED", "🟢 KEEP")
            content = content.replace("🔴 REMOVED", "🟢 KEEP")
            content = content.replace("🟡 NOT SURE", "🟢 KEEP")
            content = content.replace("🏷️ **Status:** 🟢 KEEP", "🏷️ **Status:** 🟢 KEEP")
        elif status == "removed":
            content = content.replace("⚪ NOT REVIEWED", "🔴 REMOVED")
            content = content.replace("🟢 KEEP", "🔴 REMOVED")
            content = content.replace("🟡 NOT SURE", "🔴 REMOVED")
        elif status == "not-sure":
            content = content.replace("⚪ NOT REVIEWED", "🟡 NOT SURE")
            content = content.replace("🟢 KEEP", "🟡 NOT SURE")
            content = content.replace("🔴 REMOVED", "🟡 NOT SURE")
        else:
            content = content.replace("🟢 KEEP", "⚪ NOT REVIEWED")
            content = content.replace("🔴 REMOVED", "⚪ NOT REVIEWED")
            content = content.replace("🟡 NOT SURE", "⚪ NOT REVIEWED")
        
        with open(markdown_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
        
    except Exception as e:
        print(f"Error updating {markdown_file}: {e}")
        return False


def get_next_paper_file(current_file: str, output_dir: str) -> Optional[str]:
    """
    Get the next paper file in alphabetical order.
    
    Args:
        current_file: Current markdown file path
        output_dir: Directory containing the markdown files
        
    Returns:
        Path to next paper file, or None if at the end
    """
    files = sorted([f for f in os.listdir(output_dir) if f.endswith('.md')])
    current_name = os.path.basename(current_file)
    
    try:
        current_idx = files.index(current_name)
        if current_idx < len(files) - 1:
            return os.path.join(output_dir, files[current_idx + 1])
    except ValueError:
        pass
    
    return None


def get_previous_paper_file(current_file: str, output_dir: str) -> Optional[str]:
    """
    Get the previous paper file in alphabetical order.
    
    Args:
        current_file: Current markdown file path
        output_dir: Directory containing the markdown files
        
    Returns:
        Path to previous paper file, or None if at the beginning
    """
    files = sorted([f for f in os.listdir(output_dir) if f.endswith('.md')])
    current_name = os.path.basename(current_file)
    
    try:
        current_idx = files.index(current_name)
        if current_idx > 0:
            return os.path.join(output_dir, files[current_idx - 1])
    except ValueError:
        pass
    
    return None


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
    df = pd.read_csv(input_csv).head()
    
    # Create markdown files
    print(f"Processing {len(df)} papers from {input_csv}...")
    created_files = write_paper_into_markdown(df, output_dir=output_dir)
    
    print(f"\nDone! Created {len(created_files)} markdown files in {output_dir}")
