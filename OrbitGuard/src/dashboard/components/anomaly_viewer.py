"""
Anomaly viewer component for Streamlit dashboard.

This module displays detected anomalies in interactive tables and cards.
Provides filtering, sorting, and detailed views of anomaly data.
"""

import streamlit as st
import pandas as pd
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_anomaly_table(
    anomalies: pd.DataFrame,
    max_rows: int = 50,
    show_filters: bool = True,
    selectable: bool = False
) -> Optional[pd.DataFrame]:
    """
    Display anomalies in interactive table format.
    
    Args:
        anomalies: DataFrame containing detected anomalies
        max_rows: Maximum number of rows to display
        show_filters: Whether to show filter controls
        selectable: Whether to allow row selection
        
    Returns:
        Selected rows if selectable=True, None otherwise
    """
    logger.debug(f"Rendering anomaly table with {len(anomalies)} anomalies")
    
    if anomalies.empty:
        st.info("No anomalies detected in the current dataset.")
        return None
    
    # Apply filters if enabled
    if show_filters:
        filtered_anomalies = add_filters(anomalies)
    else:
        filtered_anomalies = anomalies
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Anomalies", len(filtered_anomalies))
    
    with col2:
        if 'anomaly_score' in filtered_anomalies.columns:
            avg_score = filtered_anomalies['anomaly_score'].mean()
            st.metric("Avg Score", f"{avg_score:.3f}")
        else:
            st.metric("Avg Score", "N/A")
    
    with col3:
        if 'sensor_id' in filtered_anomalies.columns:
            unique_sensors = filtered_anomalies['sensor_id'].nunique()
        elif 'channel' in filtered_anomalies.columns:
            unique_sensors = filtered_anomalies['channel'].nunique()
        else:
            unique_sensors = 0
        st.metric("Affected Sensors", unique_sensors)
    
    with col4:
        if 'anomaly_score' in filtered_anomalies.columns:
            high_severity = len(filtered_anomalies[filtered_anomalies['anomaly_score'] >= 0.75])
            st.metric("High Severity", high_severity)
        else:
            st.metric("High Severity", "N/A")
    
    st.markdown("---")
    
    # Prepare display DataFrame
    display_df = _prepare_display_dataframe(filtered_anomalies)
    
    # Limit rows
    if len(display_df) > max_rows:
        st.warning(f"Showing top {max_rows} of {len(display_df)} anomalies. Use filters to narrow results.")
        display_df = display_df.head(max_rows)
    
    # Display table
    if selectable:
        # Use data editor for selection
        selected = st.data_editor(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Select": st.column_config.CheckboxColumn(
                    "Select",
                    help="Select anomalies for detailed view",
                    default=False
                )
            }
        )
        return selected[selected['Select']]
    else:
        # Use regular dataframe display
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        return None


def render_anomaly_card(
    anomaly: Dict[str, Any],
    show_details: bool = True,
    expandable: bool = False
) -> None:
    """
    Display detailed anomaly information in card format.
    
    Args:
        anomaly: Dictionary containing single anomaly data
        show_details: Whether to show detailed information
        expandable: Whether to make the card expandable
    """
    logger.debug(f"Rendering anomaly card for {anomaly.get('timestamp', 'unknown')}")
    
    # Extract key information
    timestamp = anomaly.get('timestamp', 'N/A')
    sensor_id = anomaly.get('sensor_id', anomaly.get('channel', 'Unknown'))
    value = anomaly.get('value', 'N/A')
    score = anomaly.get('anomaly_score', 0.0)
    
    # Determine severity
    severity = _get_severity_label(score)
    severity_color = _get_severity_color(severity)
    
    # Create card container
    if expandable:
        with st.expander(f"🚨 {sensor_id} - {timestamp}", expanded=False):
            _render_card_content(anomaly, severity, severity_color, show_details)
    else:
        with st.container():
            _render_card_content(anomaly, severity, severity_color, show_details)


def _render_card_content(
    anomaly: Dict[str, Any],
    severity: str,
    severity_color: str,
    show_details: bool
) -> None:
    """Render the content of an anomaly card."""
    
    # Header with severity badge
    col1, col2 = st.columns([3, 1])
    
    with col1:
        sensor_id = anomaly.get('sensor_id', anomaly.get('channel', 'Unknown'))
        st.markdown(f"### 📊 {sensor_id}")
    
    with col2:
        st.markdown(f"<span style='background-color: {severity_color}; color: white; padding: 5px 10px; border-radius: 5px; font-weight: bold;'>{severity}</span>", unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Timestamp", anomaly.get('timestamp', 'N/A'))
    
    with col2:
        value = anomaly.get('value', 'N/A')
        if isinstance(value, (int, float)):
            st.metric("Value", f"{value:.4f}")
        else:
            st.metric("Value", value)
    
    with col3:
        score = anomaly.get('anomaly_score', 0.0)
        st.metric("Anomaly Score", f"{score:.4f}")
    
    # Detailed information
    if show_details:
        st.markdown("---")
        st.markdown("**Additional Details:**")
        
        details_col1, details_col2 = st.columns(2)
        
        with details_col1:
            if 'anomaly_rank' in anomaly:
                st.write(f"**Rank:** {anomaly['anomaly_rank']}")
            
            if 'mean' in anomaly:
                st.write(f"**Mean:** {anomaly['mean']:.4f}")
            
            if 'std' in anomaly:
                st.write(f"**Std Dev:** {anomaly['std']:.4f}")
        
        with details_col2:
            if 'min' in anomaly:
                st.write(f"**Min:** {anomaly['min']:.4f}")
            
            if 'max' in anomaly:
                st.write(f"**Max:** {anomaly['max']:.4f}")
            
            if 'predicted_anomaly' in anomaly:
                status = "✅ Anomaly" if anomaly['predicted_anomaly'] else "✓ Normal"
                st.write(f"**Classification:** {status}")


def render_anomaly_grid(
    anomalies: pd.DataFrame,
    columns: int = 2,
    max_cards: int = 10
) -> None:
    """
    Display anomalies in a grid of cards.
    
    Args:
        anomalies: DataFrame containing anomalies
        columns: Number of columns in the grid
        max_cards: Maximum number of cards to display
    """
    logger.debug(f"Rendering anomaly grid with {len(anomalies)} anomalies")
    
    if anomalies.empty:
        st.info("No anomalies to display.")
        return
    
    # Limit number of cards
    display_anomalies = anomalies.head(max_cards)
    
    if len(anomalies) > max_cards:
        st.info(f"Showing top {max_cards} of {len(anomalies)} anomalies")
    
    # Convert to list of dicts
    anomalies_list = display_anomalies.to_dict('records')
    
    # Create grid
    for i in range(0, len(anomalies_list), columns):
        cols = st.columns(columns)
        
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(anomalies_list):
                with col:
                    render_anomaly_card(
                        anomalies_list[idx],
                        show_details=False,
                        expandable=True
                    )


def add_filters(anomalies: pd.DataFrame) -> pd.DataFrame:
    """
    Add interactive filters for anomaly data.
    
    Args:
        anomalies: DataFrame containing anomalies
        
    Returns:
        Filtered DataFrame based on user selections
    """
    logger.debug("Adding anomaly filters")
    
    with st.sidebar:
        st.markdown("### 🔍 Filters")
        
        filtered_df = anomalies.copy()
        
        # Severity filter
        if 'anomaly_score' in anomalies.columns:
            st.markdown("**Severity Level:**")
            
            severity_options = {
                'All': (0.0, 1.0),
                'Critical (≥0.9)': (0.9, 1.0),
                'High (≥0.75)': (0.75, 1.0),
                'Medium (≥0.5)': (0.5, 1.0),
                'Low (<0.5)': (0.0, 0.5)
            }
            
            severity_choice = st.selectbox(
                "Select severity",
                options=list(severity_options.keys()),
                index=0,
                label_visibility="collapsed"
            )
            
            min_score, max_score = severity_options[severity_choice]
            filtered_df = filtered_df[
                (filtered_df['anomaly_score'] >= min_score) &
                (filtered_df['anomaly_score'] <= max_score)
            ]
        
        # Sensor filter
        sensor_col = 'sensor_id' if 'sensor_id' in anomalies.columns else 'channel'
        if sensor_col in anomalies.columns:
            st.markdown("**Sensor/Channel:**")
            
            unique_sensors = sorted(anomalies[sensor_col].unique())
            selected_sensors = st.multiselect(
                "Select sensors",
                options=unique_sensors,
                default=unique_sensors,
                label_visibility="collapsed"
            )
            
            if selected_sensors:
                filtered_df = filtered_df[filtered_df[sensor_col].isin(selected_sensors)]
        
        # Time range filter
        if 'timestamp' in anomalies.columns:
            st.markdown("**Time Range:**")
            
            # Try to convert to datetime if not already
            try:
                if not pd.api.types.is_datetime64_any_dtype(anomalies['timestamp']):
                    anomalies['timestamp'] = pd.to_datetime(anomalies['timestamp'])
                
                min_time = anomalies['timestamp'].min()
                max_time = anomalies['timestamp'].max()
                
                time_range = st.slider(
                    "Select time range",
                    min_value=min_time.to_pydatetime(),
                    max_value=max_time.to_pydatetime(),
                    value=(min_time.to_pydatetime(), max_time.to_pydatetime()),
                    label_visibility="collapsed"
                )
                
                filtered_df = filtered_df[
                    (filtered_df['timestamp'] >= time_range[0]) &
                    (filtered_df['timestamp'] <= time_range[1])
                ]
            except Exception as e:
                logger.warning(f"Could not create time filter: {e}")
        
        # Display filter results
        st.markdown("---")
        st.markdown(f"**Showing:** {len(filtered_df)} / {len(anomalies)} anomalies")
        
        # Reset filters button
        if st.button("Reset Filters"):
            st.rerun()
    
    return filtered_df


def _prepare_display_dataframe(anomalies: pd.DataFrame) -> pd.DataFrame:
    """Prepare DataFrame for display with formatted columns."""
    
    display_df = anomalies.copy()
    
    # Select and order columns for display
    display_columns = []
    
    # Always include these if available
    priority_columns = ['timestamp', 'sensor_id', 'channel', 'value', 'anomaly_score', 'anomaly_rank']
    
    for col in priority_columns:
        if col in display_df.columns:
            display_columns.append(col)
    
    # Add remaining numeric columns
    for col in display_df.columns:
        if col not in display_columns and pd.api.types.is_numeric_dtype(display_df[col]):
            display_columns.append(col)
    
    # Limit to display columns
    display_df = display_df[display_columns]
    
    # Format numeric columns
    for col in display_df.select_dtypes(include=['float64', 'float32']).columns:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}" if pd.notna(x) else "N/A")
    
    # Rename columns for better display
    column_renames = {
        'sensor_id': 'Sensor',
        'channel': 'Channel',
        'timestamp': 'Timestamp',
        'value': 'Value',
        'anomaly_score': 'Score',
        'anomaly_rank': 'Rank',
        'predicted_anomaly': 'Anomaly'
    }
    
    display_df = display_df.rename(columns={k: v for k, v in column_renames.items() if k in display_df.columns})
    
    return display_df


def _get_severity_label(score: float) -> str:
    """Get severity label from anomaly score."""
    if score >= 0.9:
        return "CRITICAL"
    elif score >= 0.75:
        return "HIGH"
    elif score >= 0.5:
        return "MEDIUM"
    else:
        return "LOW"


def _get_severity_color(severity: str) -> str:
    """Get color code for severity level."""
    colors = {
        'CRITICAL': '#dc3545',  # Red
        'HIGH': '#fd7e14',      # Orange
        'MEDIUM': '#ffc107',    # Yellow
        'LOW': '#28a745'        # Green
    }
    return colors.get(severity, '#6c757d')  # Gray as default


def export_anomalies(
    anomalies: pd.DataFrame,
    format: str = 'csv'
) -> None:
    """
    Provide download button for anomaly data.
    
    Args:
        anomalies: DataFrame to export
        format: Export format ('csv' or 'json')
    """
    st.markdown("### 📥 Export Anomalies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CSV export
        csv = anomalies.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="anomalies.csv",
            mime="text/csv"
        )
    
    with col2:
        # JSON export
        json = anomalies.to_json(orient='records', indent=2)
        st.download_button(
            label="Download as JSON",
            data=json,
            file_name="anomalies.json",
            mime="application/json"
        )