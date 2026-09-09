from pathlib import Path

import plotly
from pandera.typing.pandas import DataFrame
from upsetty import Upset

from slrrag.settings import SchemaPapers


def plot_and_save_upset(df_input: DataFrame[SchemaPapers], output_html: Path | str):
    upset_fig = plot_upset(df_input)
    upset_fig.write_html(output_html)


def plot_upset(
    df_input: DataFrame[SchemaPapers], **kwargs
) -> plotly.graph_objs._figure.Figure:
    # set TRUE/FALSE if the paper exists or not for each database
    # Dynamically detect which id_{db} columns exist
    id_cols = [col for col in df_input.columns if col.startswith("id_")]
    database_names = [col.replace("id_", "") for col in id_cols]

    df_fig = df_input[["is_reference"]].copy()  # Copy to avoid writing on original df
    df_fig[database_names] = df_input[id_cols].notna()
    return Upset.generate_plot(
        df_fig[database_names + ["is_reference"]].rename(
            columns={"is_reference": "reference"}
        ),
        **kwargs,
    )
