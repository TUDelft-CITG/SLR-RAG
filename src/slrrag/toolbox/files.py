import os
from pathlib import Path

import pandas as pd
import pandera.pandas as pa
from pandera.typing import DataFrame

from slrrag.settings import (
    AUTOMATICALLY_OVERWRITE,
    PANDERA_LAZY_VALIDATION,
    SchemaPapers,
)


@pa.check_types(lazy=PANDERA_LAZY_VALIDATION)
def save_dataframe_to_csv(df: DataFrame[SchemaPapers], file_path: Path) -> None:
    """Save DataFrame to CSV with overwrite protection."""
    os.makedirs(file_path.parent, exist_ok=True)
    if check_overwrite(file_path, AUTOMATICALLY_OVERWRITE):
        df.to_csv(file_path, index=False, date_format="%Y-%m-%d")
        print(f"Results saved in {file_path}")


# --- File I/O functions ---
def check_overwrite(
    file_path: Path, automatically_overwrite: bool = AUTOMATICALLY_OVERWRITE
) -> bool:
    if file_path.exists() and not automatically_overwrite:
        user_input = input(
            f"File {file_path} already exists. Overwrite? (y/n): "
        ).lower()
        if user_input != "y":
            print("Operation cancelled by user.")
            return False
    else:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    return True


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
        ".",
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
