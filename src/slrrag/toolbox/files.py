import os
from pathlib import Path

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
