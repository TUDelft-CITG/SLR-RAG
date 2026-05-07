from upsetty import Upset
import pandas as pd
from pathlib import Path
import plotly
def plot_and_save_upset(df_input: pd.DataFrame, output_html: Path | str):
    upset_fig = plot_upset(df_input)
    upset_fig.write_html(output_html)


def plot_upset(df_input: pd.DataFrame) -> plotly.graph_objs._figure.Figure:
    # set TRUE/FALSE if the paper exists or not for each database
    # Dynamically detect which id_{db} columns exist
    id_cols = [col for col in df_input.columns if col.startswith("id_")]
    database_names = [col.replace("id_", "") for col in id_cols]

    df_fig = df_input[["is_reference"]].copy() # Copy to avoid writing on original df
    df_fig[database_names] = df_input[id_cols].notna()
    return Upset.generate_plot(
        df_fig[database_names + ["is_reference"]].rename(
            columns={"is_reference": "reference"}
        )
    )
