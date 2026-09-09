
from dash_upset import UpSet
import pandas as pd
from typing import List
import plotly.graph_objs as go
from sklearn.metrics import accuracy_score, auc, f1_score, roc_curve

# Calculate ROC curves for visualization
def calculate_roc_data(
    df_input: pd.DataFrame,
    model_columns: List[str],
    prefix_model_question: str = "main_question_answer_"
) -> go.Figure:
    y_true = df_input['is_picky_kept'].astype(int).values
    
    # Create ROC curve figure
    roc_fig = go.Figure()
    
    # Available colors for different models
    colors = ['blue', 'red', 'green', 'purple', 'orange', 'cyan', 'magenta', 'yellow']
    
    # Calculate ROC for each model
    for i, model_col in enumerate(model_columns, 1):
        if model_col in df_input.columns:
            y_scores = df_input[model_col].astype(int).values
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


# Create upset plot for binary columns intersections
def create_upset_plot(
    df_input: pd.DataFrame,
    binary_columns: List[str],
    mode = "intersect",
) -> UpSet:
    # Prepare data for upset plot - only use binary columns
    upset_data = df_input[binary_columns].copy()
    
    # Convert to boolean if not already
    for col in upset_data.columns:
        if upset_data[col].dtype != bool:
            upset_data[col] = upset_data[col].astype(bool)
    
    # Create the upset plot component using dash_upset
    return UpSet(
        id="model-upset",
        data=upset_data,
        mode=mode,
        theme="tol-light",
        inactive_color="#ffffff",
        selection_color="#d55e00",
    )

# Calculate performance metrics for each model
def calculate_performance_metrics(
    df_input: pd.DataFrame,
    model_columns: List[str],
    prefix_model_question: str = "main_question_answer_"
) -> go.Figure:
    y_true = df_input['is_picky_kept'].astype(int).values
    
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
        if model_col in df_input.columns:
            y_pred = df_input[model_col].astype(int).values
            
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