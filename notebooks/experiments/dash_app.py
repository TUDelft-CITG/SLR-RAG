# Run this app with `python dash_app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from dash import Dash, html, dash_table, dcc
from dash_upset import UpSet
import pandas as pd
from sklearn.metrics import roc_curve, auc, accuracy_score, f1_score, precision_score, recall_score
import plotly.graph_objs as go
from slrrag.settings import PATH_INPUT

prefix_model_question = "main_question_answer_"
app = Dash(__name__)

# Load real dataframe from the CSV file
df = pd.read_csv(PATH_INPUT / "result_agents_to_plot.csv")


# Rename columns for consistency
# Find all model columns (columns that start with 'main_question_answer_')
model_columns = [col for col in df.columns if col.startswith(prefix_model_question)]

# Sort by consensus_score score (descending - highest first)
df = df.sort_values('consensus_score', ascending=False).reset_index(drop=True)

df = df.dropna()

# Binary columns to color (green for 1/True, red for 0/False)
binary_columns = ["is_picky_kept"] + model_columns
# Build conditional styling
style_data_conditional = []

# Binary columns: green for True/1, red for False/0
# Handle both boolean and numeric binary columns
for col in binary_columns:
    # Check if column is boolean type (True/False) or numeric (1/0)
    if df[col].dtype == bool or df[col].dtype == object:
        # For boolean columns (True/False)
        style_data_conditional.append({
            "if": {
                "filter_query": f'{{{col}}} contains "true"',
                "column_id": col
            },
            "backgroundColor": "#90EE90",
            "color": "black"
        })
        style_data_conditional.append({
            "if": {
                "filter_query": f'{{{col}}} contains "false"',
                "column_id": col
            },
            "backgroundColor": "#FFCCCB",
            "color": "black"
        })
    else:
        # For numeric columns (1/0)
        style_data_conditional.append({
            "if": {
                "filter_query": f'{{{col}}} = 1',
                "column_id": col
            },
            "backgroundColor": "#90EE90",
            "color": "black"
        })
        style_data_conditional.append({
            "if": {
                "filter_query": f'{{{col}}} = 0',
                "column_id": col
            },
            "backgroundColor": "#FFCCCB",
            "color": "black"
        })

# consensus_score column: gradient from red (0) to green (1)
# Using multiple conditions to simulate a gradient
style_data_conditional.append({
    "if": {
        "filter_query": "{consensus_score} < 0.2",
        "column_id": "consensus_score"
    },
    "backgroundColor": "#FF0000",
    "color": "white"
})
style_data_conditional.append({
    "if": {
        "filter_query": "{consensus_score} >= 0.2 && {consensus_score} < 0.4",
        "column_id": "consensus_score"
    },
    "backgroundColor": "#FF4500",
    "color": "white"
})
style_data_conditional.append({
    "if": {
        "filter_query": "{consensus_score} >= 0.4 && {consensus_score} < 0.6",
        "column_id": "consensus_score"
    },
    "backgroundColor": "#FFA500",
    "color": "black"
})
style_data_conditional.append({
    "if": {
        "filter_query": "{consensus_score} >= 0.6 && {consensus_score} < 0.8",
        "column_id": "consensus_score"
    },
    "backgroundColor": "#9ACD32",
    "color": "black"
})
style_data_conditional.append({
    "if": {
        "filter_query": "{consensus_score} >= 0.8",
        "column_id": "consensus_score"
    },
    "backgroundColor": "#00FF00",
    "color": "black"
})

# Calculate ROC curves for visualization
def calculate_roc_data():
    y_true = df['is_picky_kept'].astype(int).values
    
    # Create ROC curve figure
    roc_fig = go.Figure()
    
    # Available colors for different models
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'cyan', 'magenta', 'yellow']
    
    # Calculate ROC for each model
    for i, model_col in enumerate(model_columns, 1):
        if model_col in df.columns:
            y_scores = df[model_col].astype(int).values
            fpr, tpr, _ = roc_curve(y_true, y_scores)
            roc_auc = auc(fpr, tpr)
            color = colors[i % len(colors)]
            
            roc_fig.add_trace(go.Scatter(
                x=fpr, y=tpr,
                mode='lines',
                name=f'Model {model_col.removeprefix(prefix_model_question)} (AUC = {roc_auc:.2f})',
                line=dict(color=color, width=2)
            ))
    
    # Add diagonal line
    roc_fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode='lines',
        name='Random Classifier',
        line=dict(color='gray', width=1, dash='dash')
    ))
    
    roc_fig.update_layout(
        title='ROC Curve: Models vs Ground Truth',
        xaxis_title='False Positive Rate',
        yaxis_title='True Positive Rate',
        xaxis=dict(range=[0, 1.05]),
        yaxis=dict(range=[0, 1.05]),
        template='plotly_white',
        height=500
    )
    
    return roc_fig

# Calculate performance metrics for each model
def calculate_performance_metrics():
    y_true = df['is_picky_kept'].astype(int).values
    
    # Dictionary to store metrics for each model
    metrics_data = {
        'Model': [],
        'Accuracy': [],
        'F1 Score': [],
        'True Positive Rate': [],
        'True Negative Rate': []
    }
    
    # Available colors for different models
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'cyan', 'magenta', 'yellow']
    model_names = []
    
    # Calculate metrics for each model
    for i, model_col in enumerate(model_columns):
        if model_col in df.columns:
            y_pred = df[model_col].astype(int).values
            
            # Calculate metrics
            accuracy = accuracy_score(y_true, y_pred)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            
            # Calculate True Positive Rate (TPR = TP / (TP + FN))
            tp = sum((y_true == 1) & (y_pred == 1))
            fn = sum((y_true == 1) & (y_pred == 0))
            tpr = tp / (tp + fn) if (tp + fn) > 0 else 0
            
            # Calculate True Negative Rate (TNR = TN / (TN + FP))
            tn = sum((y_true == 0) & (y_pred == 0))
            fp = sum((y_true == 0) & (y_pred == 1))
            tnr = tn / (tn + fp) if (tn + fp) > 0 else 0
            
            # Store metrics
            model_name = model_col.removeprefix(prefix_model_question)
            model_names.append(model_name)
            metrics_data['Model'].append(model_name)
            metrics_data['Accuracy'].append(accuracy)
            metrics_data['F1 Score'].append(f1)
            metrics_data['True Positive Rate'].append(tpr)
            metrics_data['True Negative Rate'].append(tnr)
    
    # Create data for grouped bar chart by measure
    metrics_df = pd.DataFrame(metrics_data)
    
    # Create figure with grouped bars by measure
    fig = go.Figure()
    
    # Define colors for each model
    model_colors = {}
    for i, model in enumerate(model_names):
        model_colors[model] = colors[i % len(colors)]
    
    # Add bars for each model within each measure
    for i, model in enumerate(model_names):
        model_data = metrics_df[metrics_df['Model'] == model].iloc[0]
        
        fig.add_trace(go.Bar(
            name=model,
            x=['Accuracy', 'F1 Score', 'True Positive Rate', 'True Negative Rate'],
            y=[
                model_data['Accuracy'],
                model_data['F1 Score'],
                model_data['True Positive Rate'],
                model_data['True Negative Rate']
            ],
            marker_color=model_colors[model],
            text=[
                round(model_data['Accuracy'], 3),
                round(model_data['F1 Score'], 3),
                round(model_data['True Positive Rate'], 3),
                round(model_data['True Negative Rate'], 3)
            ],
            textposition='auto',
        ))
    
    fig.update_layout(
        title='Model Performance Metrics',
        xaxis_title='Measure',
        yaxis_title='Score',
        barmode='group',
        template='plotly_white',
        height=500,
        yaxis=dict(range=[0, 1.05]),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    return fig

# Create upset plot for binary columns intersections
def create_upset_plot():
    # Prepare data for upset plot - only use binary columns
    upset_data = df[binary_columns].copy()
    
    # Convert to boolean if not already
    for col in upset_data.columns:
        if upset_data[col].dtype != bool:
            upset_data[col] = upset_data[col].astype(bool)
    
    # Create the upset plot component using dash_upset
    return UpSet(
        id="model-upset",
        data=upset_data,
        mode="intersect",
        theme="tol-light",
        inactive_color="#ffffff",
        selection_color="#d55e00",
    )

app.layout = html.Div(children=[
    html.H1(children='SLR-RAG Data Analysis'),
    html.Div(children='''
        Dash application for reviewing paper classification data.
    '''),
    dcc.Tabs(id='tabs', value='data-table', children=[
        dcc.Tab(label='Data Table', value='data-table', children=[
            html.Div([
                html.H2('Paper Review Data'),
                html.P(f'Displaying {len(df)} papers with {len(model_columns)} models'),
                dash_table.DataTable(
                    id='data-table',
                    columns=[{"name": col, "id": col} for col in df.columns],
                    data=df.to_dict('records'),
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                    },
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=style_data_conditional,
                    page_size=20,
                )
            ])
        ]),
        dcc.Tab(label='ROC Curve', value='roc-curve', children=[
            html.Div([
                html.H2('ROC Curve Analysis'),
                html.P(f'Comparing {len(model_columns)} models predictions against Ground Truth'),
                dcc.Graph(id='roc-curve', figure=calculate_roc_data())
            ])
        ]),
        dcc.Tab(label='Performance Metrics', value='performance-metrics', children=[
            html.Div([
                html.H2('Model Performance Metrics'),
                html.P(f'Comparing {len(model_columns)} models performance metrics'),
                dcc.Graph(id='performance-metrics', figure=calculate_performance_metrics())
            ])
        ]),
        dcc.Tab(label='Upset Plot', value='upset-plot', children=[
            html.Div([
                html.H2('Upset Plot: Model Intersections'),
                html.P(f'Showing intersections between {len(binary_columns)} binary sets'),
                create_upset_plot()
            ])
        ])
    ])
])

if __name__ == '__main__':
    app.run(debug=True)