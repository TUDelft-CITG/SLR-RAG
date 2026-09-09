#!/usr/bin/env python3
# Run this app with `python dash_app.py <input_csv_path>` and
# visit http://127.0.0.1:8050/ in your web browser.

import sys
import pandas as pd
from dash import Dash, dash_table, dcc, html

from slrrag.toolbox.plotly_visualze import (
    calculate_performance_metrics,
    calculate_roc_data,
    create_upset_plot,
)


def create_data_table(
    df_input, table_id="data-table", page_size=20, style_data_conditional=None
):
    """Create a styled DataTable with consistent formatting.

    Args:
        df_input: pandas DataFrame to display
        table_id: ID for the DataTable component
        page_size: Number of rows per page
        style_data_conditional: Optional conditional styling for data cells

    Returns:
        dash_table.DataTable: Configured DataTable component
    """
    return dash_table.DataTable(
        id=table_id,
        columns=[{"name": col, "id": col} for col in df_input.columns],
        data=df_input.to_dict("records"),
        style_table={"overflowX": "auto"},
        style_cell={
            "textAlign": "left",
            "padding": "10px",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_header={
            "backgroundColor": "rgb(230, 230, 230)", "fontWeight": "bold"},
        style_data_conditional=style_data_conditional or [],
        page_size=page_size,
    )


def build_conditional_styling(df_input, binary_columns):
    """Build conditional styling for the data table.

    Args:
        df_input: pandas DataFrame
        binary_columns: List of binary columns to style

    Returns:
        List of conditional styling rules
    """
    style_data_conditional = []

    # Binary columns: green for True/1, red for False/0
    # Handle both boolean and numeric binary columns
    for col in binary_columns:
        # Check if column is boolean type (True/False) or numeric (1/0)
        if df_input[col].dtype == bool or df_input[col].dtype == object:
            # For boolean columns (True/False)
            style_data_conditional.append(
                {
                    "if": {
                        "filter_query": f'{{{col}}} contains "true"',
                        "column_id": col,
                    },
                    "backgroundColor": "#90EE90",
                    "color": "black",
                }
            )
            style_data_conditional.append(
                {
                    "if": {
                        "filter_query": f'{{{col}}} contains "false"',
                        "column_id": col,
                    },
                    "backgroundColor": "#FFCCCB",
                    "color": "black",
                }
            )
        else:
            # For numeric columns (1/0)
            style_data_conditional.append(
                {
                    "if": {"filter_query": f"{{{col}}} = 1", "column_id": col},
                    "backgroundColor": "#90EE90",
                    "color": "black",
                }
            )
            style_data_conditional.append(
                {
                    "if": {"filter_query": f"{{{col}}} = 0", "column_id": col},
                    "backgroundColor": "#FFCCCB",
                    "color": "black",
                }
            )

    # consensus_score column: gradient from red (0) to green (1)
    # Using multiple conditions to simulate a gradient
    style_data_conditional.append(
        {
            "if": {
                "filter_query": "{consensus_score} < 0.2",
                "column_id": "consensus_score",
            },
            "backgroundColor": "#FF0000",
            "color": "white",
        }
    )
    style_data_conditional.append(
        {
            "if": {
                "filter_query": "{consensus_score} >= 0.2 && {consensus_score} < 0.4",
                "column_id": "consensus_score",
            },
            "backgroundColor": "#FF4500",
            "color": "white",
        }
    )
    style_data_conditional.append(
        {
            "if": {
                "filter_query": "{consensus_score} >= 0.4 && {consensus_score} < 0.6",
                "column_id": "consensus_score",
            },
            "backgroundColor": "#FFA500",
            "color": "black",
        }
    )
    style_data_conditional.append(
        {
            "if": {
                "filter_query": "{consensus_score} >= 0.6 && {consensus_score} < 0.8",
                "column_id": "consensus_score",
            },
            "backgroundColor": "#9ACD32",
            "color": "black",
        }
    )
    style_data_conditional.append(
        {
            "if": {
                "filter_query": "{consensus_score} >= 0.8",
                "column_id": "consensus_score",
            },
            "backgroundColor": "#00FF00",
            "color": "black",
        }
    )

    return style_data_conditional


def create_data_table_tab(
    df_input: pd.DataFrame,
    model_columns: list[str] | None = None,
    style_data_conditional: list[dict] | None = None,
) -> html.Div:
    """Create the Data Table tab content.

    Args:
        df_input: pandas DataFrame to display
        model_columns: Optional list of model columns for display count
        style_data_conditional: Optional conditional styling rules

    Returns:
        html.Div: Data Table tab content
    """
    if style_data_conditional is None:
        binary_columns = model_columns or []
        style_data_conditional = build_conditional_styling(df_input, binary_columns)

    return html.Div(
        [
            html.H2("Paper Review Data"),
            html.P(
                f"Displaying {len(df_input)} papers with {len(model_columns) if model_columns else 0} models"
            ),
            create_data_table(
                df_input,
                table_id="data-table",
                page_size=20,
                style_data_conditional=style_data_conditional,
            ),
        ]
    )


def create_roc_curve_tab(
    df_input: pd.DataFrame, model_columns: list[str] | None = None
) -> html.Div:
    """Create the ROC Curve tab content.

    Args:
        df_input: pandas DataFrame to display
        model_columns: Optional list of model columns

    Returns:
        html.Div: ROC Curve tab content
    """
    if model_columns is None:
        model_columns = []

    return html.Div(
        [
            html.H2("ROC Curve Analysis"),
            html.P(
                f"Comparing {len(model_columns)} models predictions against Ground Truth"
            ),
            dcc.Graph(
                id="roc-curve",
                figure=calculate_roc_data(df_input, model_columns),
            ),
        ]
    )


def create_performance_metrics_tab(
    df_input: pd.DataFrame, model_columns: list[str] | None = None
) -> html.Div:
    """Create the Performance Metrics tab content.

    Args:
        df_input: pandas DataFrame to display
        model_columns: Optional list of model columns

    Returns:
        html.Div: Performance Metrics tab content
    """
    if model_columns is None:
        model_columns = []

    return html.Div(
        [
            html.H2("Model Performance Metrics"),
            html.P(
                f"Comparing {len(model_columns)} models performance metrics"
            ),
            dcc.Graph(
                id="performance-metrics",
                figure=calculate_performance_metrics(df_input, model_columns),
            ),
        ]
    )


def create_upset_plot_tab(
    df_input: pd.DataFrame,
    binary_columns: list[str] | None = None,
) -> html.Div:
    """Create the Upset Plot tab content.

    Args:
        df_input: pandas DataFrame to display
        binary_columns: Optional list of binary columns

    Returns:
        html.Div: Upset Plot tab content
    """
    if binary_columns is None:
        binary_columns = []

    return html.Div(
        [
            html.H2("Upset Plot: Model Intersections"),
            html.P(
                f"Showing intersections between {len(binary_columns)} binary sets"
            ),
            create_upset_plot(df_input, binary_columns),
        ]
    )


def create_app_layout(
    df_input: pd.DataFrame,
    model_columns: list[str] | None = None,
    binary_columns: list[str] | None = None,
) -> html.Div:
    """Create the Dash app layout.

    Args:
        df_input: pandas DataFrame to display
        model_columns: Optional list of model columns
        binary_columns: Optional list of binary columns

    Returns:
        html.Div: Dash app layout
    """
    return html.Div(
        children=[
            html.H1(children="SLR-RAG Data Analysis"),
            html.Div(
                children="""
            Dash application for reviewing paper classification data.
        """
            ),
            dcc.Tabs(
                id="tabs",
                value="data-table",
                children=[
                    dcc.Tab(
                        label="Data Table",
                        value="data-table",
                        children=[create_data_table_tab(df_input, model_columns)],
                    ),
                    dcc.Tab(
                        label="ROC Curve",
                        value="roc-curve",
                        children=[create_roc_curve_tab(df_input, model_columns)],
                    ),
                    dcc.Tab(
                        label="Performance Metrics",
                        value="performance-metrics",
                        children=[create_performance_metrics_tab(df_input, model_columns)],
                    ),
                    dcc.Tab(
                        label="Upset Plot",
                        value="upset-plot",
                        children=[create_upset_plot_tab(df_input, binary_columns)],
                    ),
                ],
            ),
        ]
    )


if __name__ == "__main__":
    # Check if input CSV path is provided
    if len(sys.argv) < 2:
        print("Usage: python dash_app.py <input_csv_path>")
        print("Please provide the path to the input CSV file.")
        sys.exit(1)

    input_csv_path = sys.argv[1]
    prefix_model_question = "main_question_answer_"
    app = Dash(__name__)

    # Load and preprocess data
    df = pd.read_csv(input_csv_path)

    # Find all model columns (columns that start with 'main_question_answer_')
    model_columns = [
        col for col in df.columns if col.startswith(prefix_model_question)]

    # Sort by consensus_score score (descending - highest first)
    df = df.sort_values("consensus_score",
                        ascending=False).reset_index(drop=True)

    # Drop NA values
    df = df.dropna()

    # Binary columns to color (green for 1/True, red for 0/False)
    binary_columns = ["is_picky_kept"] + model_columns

    # Create app layout
    app.layout = create_app_layout(
        df, model_columns, binary_columns
    )

    app.run(debug=True)
