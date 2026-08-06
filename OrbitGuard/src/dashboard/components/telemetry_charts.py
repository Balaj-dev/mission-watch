"""
Telemetry visualization component for Streamlit dashboard.

This module creates time-series charts and visualizations for telemetry data.
Uses Plotly for interactive, publication-quality charts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, List, Dict, Any
import numpy as np
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def plot_telemetry_timeseries(
    data: pd.DataFrame,
    anomalies: Optional[pd.DataFrame] = None,
    sensor_col: str = 'sensor_id',
    value_col: str = 'value',
    time_col: str = 'timestamp',
    max_sensors: int = 8,
    height: int = 600
) -> None:
    """
    Plot time-series telemetry data with anomaly markers.
    
    Args:
        data: Telemetry DataFrame with timestamp and sensor readings
        anomalies: Optional DataFrame containing detected anomalies
        sensor_col: Column name for sensor identifier
        value_col: Column name for sensor values
        time_col: Column name for timestamps
        max_sensors: Maximum number of sensors to plot
        height: Chart height in pixels
    """
    logger.debug(f"Plotting telemetry time-series for {len(data)} records")
    
    if data.empty:
        st.warning("No telemetry data to display.")
        return
    
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(data[time_col]):
        data[time_col] = pd.to_datetime(data[time_col])
    
    # Get unique sensors
    if sensor_col == 'sensor_id' and sensor_col not in data.columns:
        sensor_col = 'channel'
    
    sensors = data[sensor_col].unique()
    
    if len(sensors) > max_sensors:
        st.info(f"Showing {max_sensors} of {len(sensors)} sensors. Use filters to view specific sensors.")
        sensors = sensors[:max_sensors]
    
    # Create figure
    fig = go.Figure()
    
    # Plot each sensor
    for sensor in sensors:
        sensor_data = data[data[sensor_col] == sensor].sort_values(time_col)
        
        fig.add_trace(go.Scatter(
            x=sensor_data[time_col],
            y=sensor_data[value_col],
            mode='lines',
            name=sensor,
            line=dict(width=1.5),
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Time: %{x}<br>' +
                         'Value: %{y:.4f}<br>' +
                         '<extra></extra>'
        ))
    
    # Add anomaly markers if provided
    if anomalies is not None and not anomalies.empty:
        # Ensure anomalies have datetime timestamps
        if not pd.api.types.is_datetime64_any_dtype(anomalies[time_col]):
            anomalies[time_col] = pd.to_datetime(anomalies[time_col])
        
        for sensor in sensors:
            sensor_anomalies = anomalies[anomalies[sensor_col] == sensor]
            
            if not sensor_anomalies.empty:
                fig.add_trace(go.Scatter(
                    x=sensor_anomalies[time_col],
                    y=sensor_anomalies[value_col],
                    mode='markers',
                    name=f'{sensor} (Anomalies)',
                    marker=dict(
                        size=10,
                        color='red',
                        symbol='x',
                        line=dict(width=2, color='darkred')
                    ),
                    hovertemplate='<b>ANOMALY</b><br>' +
                                 'Sensor: %{fullData.name}<br>' +
                                 'Time: %{x}<br>' +
                                 'Value: %{y:.4f}<br>' +
                                 '<extra></extra>'
                ))
    
    # Update layout
    fig.update_layout(
        title='Telemetry Time-Series Data',
        xaxis_title='Timestamp',
        yaxis_title='Sensor Value',
        hovermode='closest',
        height=height,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        template='plotly_white'
    )
    
    # Display chart
    st.plotly_chart(fig, use_container_width=True)


def plot_anomaly_distribution(
    anomalies: pd.DataFrame,
    sensor_col: str = 'sensor_id',
    score_col: str = 'anomaly_score',
    time_col: str = 'timestamp'
) -> None:
    """
    Plot distribution of anomalies (histogram/heatmap).
    
    Args:
        anomalies: DataFrame containing detected anomalies
        sensor_col: Column name for sensor identifier
        score_col: Column name for anomaly scores
        time_col: Column name for timestamps
    """
    logger.debug(f"Plotting anomaly distribution for {len(anomalies)} anomalies")
    
    if anomalies.empty:
        st.info("No anomalies to display.")
        return
    
    # Adjust sensor column name
    if sensor_col == 'sensor_id' and sensor_col not in anomalies.columns:
        sensor_col = 'channel'
    
    # Create tabs for different visualizations
    tab1, tab2, tab3 = st.tabs(["📊 By Sensor", "📈 Score Distribution", "🕐 Temporal Distribution"])
    
    with tab1:
        # Anomalies by sensor (bar chart)
        sensor_counts = anomalies[sensor_col].value_counts().reset_index()
        sensor_counts.columns = ['Sensor', 'Count']
        
        fig = px.bar(
            sensor_counts,
            x='Sensor',
            y='Count',
            title='Anomalies by Sensor/Channel',
            color='Count',
            color_continuous_scale='Reds',
            text='Count'
        )
        
        fig.update_traces(textposition='outside')
        fig.update_layout(
            xaxis_title='Sensor/Channel',
            yaxis_title='Number of Anomalies',
            showlegend=False,
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Anomaly score distribution (histogram)
        if score_col in anomalies.columns:
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=anomalies[score_col],
                nbinsx=30,
                marker_color='indianred',
                opacity=0.7,
                name='Anomaly Scores'
            ))
            
            # Add vertical lines for severity thresholds
            fig.add_vline(x=0.5, line_dash="dash", line_color="orange", 
                         annotation_text="Medium", annotation_position="top")
            fig.add_vline(x=0.75, line_dash="dash", line_color="red", 
                         annotation_text="High", annotation_position="top")
            fig.add_vline(x=0.9, line_dash="dash", line_color="darkred", 
                         annotation_text="Critical", annotation_position="top")
            
            fig.update_layout(
                title='Anomaly Score Distribution',
                xaxis_title='Anomaly Score',
                yaxis_title='Frequency',
                height=400,
                template='plotly_white',
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean Score", f"{anomalies[score_col].mean():.3f}")
            with col2:
                st.metric("Median Score", f"{anomalies[score_col].median():.3f}")
            with col3:
                st.metric("Max Score", f"{anomalies[score_col].max():.3f}")
            with col4:
                st.metric("Std Dev", f"{anomalies[score_col].std():.3f}")
        else:
            st.warning("Anomaly scores not available in data.")
    
    with tab3:
        # Temporal distribution (time-based heatmap or line chart)
        if time_col in anomalies.columns:
            # Ensure datetime
            if not pd.api.types.is_datetime64_any_dtype(anomalies[time_col]):
                anomalies[time_col] = pd.to_datetime(anomalies[time_col])
            
            # Group by hour
            anomalies['hour'] = anomalies[time_col].dt.floor('h')
            temporal_counts = anomalies.groupby('hour').size().reset_index(name='count')
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=temporal_counts['hour'],
                y=temporal_counts['count'],
                mode='lines+markers',
                line=dict(color='red', width=2),
                marker=dict(size=6),
                fill='tozeroy',
                fillcolor='rgba(255,0,0,0.1)'
            ))
            
            fig.update_layout(
                title='Anomalies Over Time',
                xaxis_title='Time',
                yaxis_title='Number of Anomalies',
                height=400,
                template='plotly_white',
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Timestamp information not available.")


def plot_feature_importance(
    model: Any,
    feature_names: Optional[List[str]] = None,
    top_n: int = 15
) -> None:
    """
    Plot feature importance from ML model.
    
    Args:
        model: Trained anomaly detection model
        feature_names: List of feature names
        top_n: Number of top features to display
    """
    logger.debug("Plotting feature importance")
    
    try:
        # Try to extract feature importance
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
        elif hasattr(model, 'model') and hasattr(model.model, 'feature_importances_'):
            importances = model.model.feature_importances_
        else:
            st.info("Feature importance not available for this model type.")
            return
        
        # Get feature names
        if feature_names is None:
            if hasattr(model, 'feature_cols'):
                feature_names = model.feature_cols
            else:
                feature_names = [f'Feature {i}' for i in range(len(importances))]
        
        # Create DataFrame
        importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': importances
        }).sort_values('Importance', ascending=False).head(top_n)
        
        # Create bar chart
        fig = px.bar(
            importance_df,
            x='Importance',
            y='Feature',
            orientation='h',
            title=f'Top {top_n} Feature Importances',
            color='Importance',
            color_continuous_scale='Blues',
            text='Importance'
        )
        
        fig.update_traces(texttemplate='%{text:.4f}', textposition='outside')
        fig.update_layout(
            xaxis_title='Importance Score',
            yaxis_title='Feature',
            height=max(400, top_n * 30),
            template='plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        logger.error(f"Failed to plot feature importance: {e}")
        st.error("Could not generate feature importance plot.")


def plot_sensor_heatmap(
    data: pd.DataFrame,
    sensor_col: str = 'sensor_id',
    value_col: str = 'value',
    time_col: str = 'timestamp',
    aggregation: str = 'mean'
) -> None:
    """
    Plot heatmap of sensor values over time.
    
    Args:
        data: Telemetry DataFrame
        sensor_col: Column name for sensor identifier
        value_col: Column name for values
        time_col: Column name for timestamps
        aggregation: Aggregation method ('mean', 'max', 'min', 'std')
    """
    logger.debug("Plotting sensor heatmap")
    
    if data.empty:
        st.warning("No data to display.")
        return
    
    # Adjust sensor column
    if sensor_col == 'sensor_id' and sensor_col not in data.columns:
        sensor_col = 'channel'
    
    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(data[time_col]):
        data[time_col] = pd.to_datetime(data[time_col])
    
    # Create time bins (hourly)
    data['time_bin'] = data[time_col].dt.floor('h')
    
    # Pivot data
    if aggregation == 'mean':
        pivot_data = data.pivot_table(
            values=value_col,
            index=sensor_col,
            columns='time_bin',
            aggfunc='mean'
        )
    elif aggregation == 'max':
        pivot_data = data.pivot_table(
            values=value_col,
            index=sensor_col,
            columns='time_bin',
            aggfunc='max'
        )
    elif aggregation == 'min':
        pivot_data = data.pivot_table(
            values=value_col,
            index=sensor_col,
            columns='time_bin',
            aggfunc='min'
        )
    elif aggregation == 'std':
        pivot_data = data.pivot_table(
            values=value_col,
            index=sensor_col,
            columns='time_bin',
            aggfunc='std'
        )
    else:
        pivot_data = data.pivot_table(
            values=value_col,
            index=sensor_col,
            columns='time_bin',
            aggfunc='mean'
        )
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=pivot_data.values,
        x=pivot_data.columns,
        y=pivot_data.index,
        colorscale='RdYlBu_r',
        hovertemplate='Sensor: %{y}<br>Time: %{x}<br>Value: %{z:.4f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Sensor Values Heatmap ({aggregation.capitalize()})',
        xaxis_title='Time',
        yaxis_title='Sensor',
        height=max(400, len(pivot_data) * 30),
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_correlation_matrix(
    data: pd.DataFrame,
    features: Optional[List[str]] = None
) -> None:
    """
    Plot correlation matrix of sensor features.
    
    Args:
        data: DataFrame with sensor data
        features: List of feature columns to include
    """
    logger.debug("Plotting correlation matrix")
    
    if data.empty:
        st.warning("No data to display.")
        return
    
    # Select numeric columns if features not specified
    if features is None:
        features = data.select_dtypes(include=[np.number]).columns.tolist()
        # Exclude certain columns
        exclude = ['is_anomaly', 'predicted_anomaly', 'anomaly_score', 'anomaly_rank']
        features = [f for f in features if f not in exclude]
    
    if len(features) < 2:
        st.info("Not enough numeric features for correlation analysis.")
        return
    
    # Calculate correlation matrix
    corr_matrix = data[features].corr()
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        colorscale='RdBu',
        zmid=0,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        hovertemplate='%{x} vs %{y}<br>Correlation: %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title='Feature Correlation Matrix',
        height=max(500, len(features) * 40),
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def plot_anomaly_timeline(
    anomalies: pd.DataFrame,
    sensor_col: str = 'sensor_id',
    time_col: str = 'timestamp',
    score_col: str = 'anomaly_score'
) -> None:
    """
    Plot timeline view of anomalies with severity indicators.
    
    Args:
        anomalies: DataFrame containing anomalies
        sensor_col: Column name for sensor identifier
        time_col: Column name for timestamps
        score_col: Column name for anomaly scores
    """
    logger.debug("Plotting anomaly timeline")
    
    if anomalies.empty:
        st.info("No anomalies to display.")
        return
    
    # Adjust sensor column
    if sensor_col == 'sensor_id' and sensor_col not in anomalies.columns:
        sensor_col = 'channel'
    
    # Ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(anomalies[time_col]):
        anomalies[time_col] = pd.to_datetime(anomalies[time_col])
    
    # Create severity categories
    def get_severity(score):
        if score >= 0.9:
            return 'Critical'
        elif score >= 0.75:
            return 'High'
        elif score >= 0.5:
            return 'Medium'
        else:
            return 'Low'
    
    anomalies['severity'] = anomalies[score_col].apply(get_severity)
    
    # Create scatter plot
    fig = px.scatter(
        anomalies,
        x=time_col,
        y=sensor_col,
        color='severity',
        size=score_col,
        hover_data=[score_col, 'value'] if 'value' in anomalies.columns else [score_col],
        title='Anomaly Timeline',
        color_discrete_map={
            'Critical': '#dc3545',
            'High': '#fd7e14',
            'Medium': '#ffc107',
            'Low': '#28a745'
        },
        category_orders={'severity': ['Critical', 'High', 'Medium', 'Low']}
    )
    
    fig.update_layout(
        xaxis_title='Time',
        yaxis_title='Sensor/Channel',
        height=max(400, anomalies[sensor_col].nunique() * 40),
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)