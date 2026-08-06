"""
Mission Watch - Main Streamlit Dashboard Application.

This is the entry point for the Mission Watch telemetry triage system.
Orchestrates data loading, agent execution, and result visualization.
"""

import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional
import sys
from pathlib import Path
import time

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.logger import setup_logger
from src.utils.config_loader import load_config, get_config_value
from src.data.loader import load_telemetry_data
from src.data.preprocessor import preprocess_telemetry
from src.agents.signal_analyst.detector import detect_anomalies, run_detection_pipeline
from src.agents.advisor.advisor import generate_batch_briefs, create_advisor_pipeline
from src.agents.advisor.watsonx_client import initialize_client
from src.dashboard.components.anomaly_viewer import (
    render_anomaly_table,
    render_anomaly_grid,
    export_anomalies
)
from src.dashboard.components.telemetry_charts import (
    plot_telemetry_timeseries,
    plot_anomaly_distribution,
    plot_anomaly_timeline,
    plot_sensor_heatmap
)
from src.dashboard.components.ops_brief_display import (
    render_brief,
    render_brief_history,
    export_brief
)

logger = setup_logger(__name__)


def main():
    """
    Main application entry point.
    
    Initializes the dashboard, loads data, runs agents, and displays results.
    """
    # Page configuration
    st.set_page_config(
        page_title="Mission Watch - Spacecraft Telemetry Triage",
        page_icon="🛰️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 3rem;
            font-weight: bold;
            color: #1f77b4;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
            text-align: center;
            margin-bottom: 2rem;
        }
        .stAlert {
            margin-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="main-header">🛰️ Mission Watch</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Multi-Agent Anomaly Triage System for Spacecraft Telemetry</div>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    if 'anomalies_detected' not in st.session_state:
        st.session_state.anomalies_detected = False
    if 'briefs_generated' not in st.session_state:
        st.session_state.briefs_generated = False
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Data source selection
        st.markdown("### 📁 Data Source")
        data_source = st.text_input(
            "Data path",
            value="data/processed/telemetry_dataset.csv",
            help="Path to telemetry data file"
        )
        
        # Model configuration
        st.markdown("### 🤖 Detection Model")
        model_type = st.selectbox(
            "Model type",
            options=['isolation_forest', 'zscore', 'iqr', 'ensemble'],
            index=0,
            help="Anomaly detection algorithm"
        )
        
        contamination = st.slider(
            "Contamination",
            min_value=0.01,
            max_value=0.5,
            value=0.05,
            step=0.01,
            help="Expected proportion of anomalies"
        )
        
        threshold = st.slider(
            "Anomaly threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.05,
            help="Minimum score to classify as anomaly"
        )
        
        # Advisor configuration
        st.markdown("### 💬 Advisor Settings")
        brief_mode = st.radio(
            "Brief generation mode",
            options=['individual', 'consolidated'],
            index=1,
            help="Generate separate briefs or one consolidated brief"
        )
        
        max_briefs = st.number_input(
            "Max briefs to generate",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum number of individual briefs (if individual mode)"
        )
        
        st.markdown("---")
        
        # Action buttons
        if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
            st.session_state.run_analysis = True
        
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    # Main content area
    if st.session_state.get('run_analysis', False):
        run_full_pipeline(
            data_source=data_source,
            model_type=model_type,
            contamination=contamination,
            threshold=threshold,
            brief_mode=brief_mode,
            max_briefs=max_briefs
        )
    else:
        # Welcome screen
        display_welcome_screen()


def run_full_pipeline(
    data_source: str,
    model_type: str,
    contamination: float,
    threshold: float,
    brief_mode: str,
    max_briefs: int
):
    """
    Execute the complete analysis pipeline.
    
    Args:
        data_source: Path to telemetry data
        model_type: Type of detection model
        contamination: Contamination parameter
        threshold: Anomaly threshold
        brief_mode: Brief generation mode
        max_briefs: Maximum number of briefs
    """
    logger.info("Starting full analysis pipeline")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Load data
        status_text.text("📥 Loading telemetry data...")
        progress_bar.progress(10)
        
        telemetry_data = load_data_pipeline(data_source)
        
        if telemetry_data is None or telemetry_data.empty:
            st.error("Failed to load data. Please check the data source path.")
            return
        
        st.session_state.telemetry_data = telemetry_data
        st.session_state.data_loaded = True
        
        progress_bar.progress(25)
        
        # Step 2: Run Signal Analyst
        status_text.text("🔍 Detecting anomalies...")
        progress_bar.progress(40)
        
        results = run_agents(
            telemetry_data,
            model_type=model_type,
            contamination=contamination,
            threshold=threshold
        )
        
        st.session_state.detection_results = results
        st.session_state.anomalies_detected = True
        
        progress_bar.progress(60)
        
        # Step 3: Run Advisor
        if results['anomalies'] is not None and not results['anomalies'].empty:
            status_text.text("💬 Generating operational briefs...")
            progress_bar.progress(75)
            
            # Limit anomalies for brief generation
            anomalies_for_briefs = results['anomalies'].head(max_briefs)
            
            briefs = generate_batch_briefs(
                anomalies_for_briefs.to_dict('records'),
                mode=brief_mode
            )
            
            st.session_state.briefs = briefs
            st.session_state.briefs_generated = True
        else:
            st.session_state.briefs = []
            st.session_state.briefs_generated = False
        
        progress_bar.progress(90)
        
        # Step 4: Display results
        status_text.text("📊 Rendering results...")
        progress_bar.progress(100)
        
        time.sleep(0.5)  # Brief pause for UX
        
        status_text.empty()
        progress_bar.empty()
        
        # Display results
        display_results(results)
        
        logger.info("Pipeline execution complete")
    
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        st.error(f"❌ Analysis failed: {str(e)}")
        st.exception(e)


def load_data_pipeline(data_source: str) -> Optional[pd.DataFrame]:
    """
    Load and preprocess telemetry data.
    
    Args:
        data_source: Path to data file
        
    Returns:
        Preprocessed telemetry DataFrame or None if failed
    """
    logger.info(f"Loading data from {data_source}")
    
    try:
        # Load data
        telemetry_data, metadata = load_telemetry_data(data_source)
        
        # Preprocess
        processed_data = preprocess_telemetry(telemetry_data)
        
        logger.info(f"Data loaded successfully: {len(processed_data)} records")
        
        return processed_data
    
    except Exception as e:
        logger.error(f"Failed to load data: {str(e)}", exc_info=True)
        return None


def run_agents(
    telemetry_data: pd.DataFrame,
    model_type: str = 'isolation_forest',
    contamination: float = 0.05,
    threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Execute Signal Analyst and Advisor agents.
    
    Args:
        telemetry_data: Preprocessed telemetry data
        model_type: Type of detection model
        contamination: Contamination parameter
        threshold: Anomaly threshold
        
    Returns:
        Dictionary containing agent results
    """
    logger.info("Running agents")
    
    try:
        # Run Signal Analyst
        anomalies_df = detect_anomalies(
            telemetry_data,
            model_type=model_type,
            train_model_flag=True,
            contamination=contamination,
            threshold=threshold
        )
        
        # Extract only detected anomalies
        detected_anomalies = anomalies_df[anomalies_df['predicted_anomaly'] == 1].copy()
        
        logger.info(f"Detected {len(detected_anomalies)} anomalies")
        
        return {
            'anomalies': detected_anomalies,
            'all_predictions': anomalies_df,
            'summary': {
                'total_records': len(telemetry_data),
                'anomalies_detected': len(detected_anomalies),
                'anomaly_rate': len(detected_anomalies) / len(telemetry_data) * 100,
                'model_type': model_type
            }
        }
    
    except Exception as e:
        logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
        raise


def display_results(results: Dict[str, Any]) -> None:
    """
    Render dashboard components with agent results.
    
    Args:
        results: Dictionary containing anomalies and briefs
    """
    logger.info("Displaying results")
    
    anomalies = results['anomalies']
    all_predictions = results['all_predictions']
    summary = results['summary']
    
    # Summary metrics
    st.markdown("## 📊 Analysis Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Records",
            f"{summary['total_records']:,}"
        )
    
    with col2:
        st.metric(
            "Anomalies Detected",
            f"{summary['anomalies_detected']:,}",
            delta=f"{summary['anomaly_rate']:.2f}%"
        )
    
    with col3:
        if 'anomaly_score' in anomalies.columns and not anomalies.empty:
            avg_score = anomalies['anomaly_score'].mean()
            st.metric(
                "Avg Anomaly Score",
                f"{avg_score:.3f}"
            )
        else:
            st.metric("Avg Anomaly Score", "N/A")
    
    with col4:
        st.metric(
            "Model Type",
            summary['model_type'].replace('_', ' ').title()
        )
    
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Anomalies",
        "📈 Visualizations",
        "💬 Operational Briefs",
        "📊 Raw Data"
    ])
    
    with tab1:
        st.markdown("## 🔍 Detected Anomalies")
        
        if not anomalies.empty:
            # Display options
            view_mode = st.radio(
                "View mode",
                options=['Table', 'Grid'],
                horizontal=True
            )
            
            if view_mode == 'Table':
                render_anomaly_table(anomalies, max_rows=100, show_filters=True)
            else:
                render_anomaly_grid(anomalies, columns=2, max_cards=20)
            
            # Export option
            st.markdown("---")
            export_anomalies(anomalies)
        else:
            st.info("✅ No anomalies detected in the telemetry data.")
    
    with tab2:
        st.markdown("## 📈 Telemetry Visualizations")
        
        if not anomalies.empty:
            # Time-series plot
            st.markdown("### Time-Series Data with Anomalies")
            plot_telemetry_timeseries(
                st.session_state.telemetry_data,
                anomalies=anomalies,
                max_sensors=6
            )
            
            st.markdown("---")
            
            # Anomaly distribution
            st.markdown("### Anomaly Analysis")
            plot_anomaly_distribution(anomalies)
            
            st.markdown("---")
            
            # Anomaly timeline
            st.markdown("### Anomaly Timeline")
            plot_anomaly_timeline(anomalies)
        else:
            st.info("No anomalies to visualize.")
    
    with tab3:
        st.markdown("## 💬 Operational Briefs")
        
        if st.session_state.get('briefs_generated', False):
            briefs = st.session_state.briefs
            
            if briefs:
                for i, brief in enumerate(briefs, 1):
                    render_brief(
                        brief,
                        title=f"Brief #{i}",
                        expandable=True
                    )
                    
                    if i < len(briefs):
                        st.markdown("---")
            else:
                st.warning("No briefs were generated.")
        else:
            st.info("Operational briefs will appear here after analysis.")
    
    with tab4:
        st.markdown("## 📊 Raw Data")
        
        # Show all predictions
        st.markdown("### All Predictions")
        st.dataframe(
            all_predictions.head(1000),
            use_container_width=True,
            hide_index=True
        )
        
        # Download options
        st.markdown("---")
        st.markdown("### Download Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv = all_predictions.to_csv(index=False)
            st.download_button(
                label="Download All Predictions (CSV)",
                data=csv,
                file_name="all_predictions.csv",
                mime="text/csv"
            )
        
        with col2:
            if not anomalies.empty:
                csv = anomalies.to_csv(index=False)
                st.download_button(
                    label="Download Anomalies Only (CSV)",
                    data=csv,
                    file_name="anomalies_only.csv",
                    mime="text/csv"
                )


def display_welcome_screen():
    """Display welcome screen with instructions."""
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 👋 Welcome to Mission Watch
        
        **Mission Watch** is a multi-agent anomaly triage system designed for spacecraft telemetry monitoring.
        
        ### 🎯 Features
        
        - **🔍 Signal Analyst Agent**: Detects anomalies using machine learning (Isolation Forest, statistical methods)
        - **💬 Advisor Agent**: Generates plain-language operational briefs using IBM Granite LLM
        - **📊 Interactive Dashboard**: Visualize telemetry data and anomalies in real-time
        - **📈 Advanced Analytics**: Time-series plots, distribution analysis, and correlation matrices
        
        ### 🚀 Getting Started
        
        1. **Configure** your analysis in the sidebar:
           - Select data source
           - Choose detection model
           - Set anomaly threshold
           - Configure brief generation
        
        2. **Run Analysis** by clicking the "🚀 Run Analysis" button
        
        3. **Explore Results** across multiple tabs:
           - View detected anomalies
           - Analyze visualizations
           - Read operational briefs
           - Export data
        
        ### 📚 Documentation
        
        - **AGENTS.md**: Development guidelines and architecture
        - **PROJECT_STRUCTURE.md**: Detailed module documentation
        - **README.md**: Setup and usage instructions
        
        ### ⚙️ System Status
        """)
        
        # System status
        status_col1, status_col2, status_col3 = st.columns(3)
        
        with status_col1:
            st.metric("Data Pipeline", "✅ Ready")
        
        with status_col2:
            st.metric("Signal Analyst", "✅ Ready")
        
        with status_col3:
            # Check if watsonx is configured
            try:
                client = initialize_client()
                if client.mock_mode:
                    st.metric("Advisor Agent", "⚠️ Mock Mode")
                else:
                    st.metric("Advisor Agent", "✅ Ready")
            except:
                st.metric("Advisor Agent", "⚠️ Mock Mode")
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        
        st.info("""
        **Default Configuration:**
        - Model: Isolation Forest
        - Contamination: 5%
        - Threshold: 0.7
        - Brief Mode: Consolidated
        """)
        
        st.markdown("### 🔗 Quick Links")
        
        st.markdown("""
        - [NASA SMAP Mission](https://smap.jpl.nasa.gov/)
        - [IBM watsonx](https://www.ibm.com/watsonx)
        - [Granite Models](https://www.ibm.com/granite)
        """)
        
        st.markdown("### 💡 Tips")
        
        st.markdown("""
        - Start with default settings
        - Use filters to focus on specific sensors
        - Export results for further analysis
        - Adjust threshold to tune sensitivity
        """)


if __name__ == "__main__":
    main()