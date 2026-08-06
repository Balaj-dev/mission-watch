"""
Operational brief display component for Streamlit dashboard.

This module renders AI-generated operational briefs from the Advisor agent.
Provides formatted display, history tracking, and export capabilities.
"""

import streamlit as st
from typing import List, Dict, Any, Optional
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def render_brief(
    brief_text: str,
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    expandable: bool = False
) -> None:
    """
    Display formatted operational brief.
    
    Args:
        brief_text: Plain-language operational brief from Advisor
        title: Optional title for the brief
        metadata: Optional metadata to display
        expandable: Whether to make the brief expandable
    """
    logger.debug("Rendering operational brief")
    
    if not brief_text:
        st.warning("No brief available to display.")
        return
    
    # Create container
    if expandable:
        with st.expander("📋 Operational Brief", expanded=True):
            _render_brief_content(brief_text, title, metadata)
    else:
        with st.container():
            _render_brief_content(brief_text, title, metadata)


def _render_brief_content(
    brief_text: str,
    title: Optional[str],
    metadata: Optional[Dict[str, Any]]
) -> None:
    """Render the content of an operational brief."""
    
    # Header
    if title:
        st.markdown(f"## {title}")
    else:
        st.markdown("## 📋 Operational Brief")
    
    # Metadata section
    if metadata:
        with st.expander("ℹ️ Brief Metadata", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                if 'generated_at' in metadata:
                    st.write(f"**Generated:** {metadata['generated_at']}")
                if 'model' in metadata:
                    st.write(f"**Model:** {metadata['model']}")
                if 'num_anomalies' in metadata:
                    st.write(f"**Anomalies Analyzed:** {metadata['num_anomalies']}")
            
            with col2:
                if 'severity' in metadata:
                    st.write(f"**Severity:** {metadata['severity']}")
                if 'confidence' in metadata:
                    st.write(f"**Confidence:** {metadata['confidence']}")
                if 'analyst' in metadata:
                    st.write(f"**Analyst:** {metadata['analyst']}")
    
    st.markdown("---")
    
    # Brief content
    st.markdown(brief_text)
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📥 Export Brief", key="export_brief_btn"):
            export_brief(brief_text, format='markdown')
    
    with col2:
        if st.button("📋 Copy to Clipboard", key="copy_brief_btn"):
            st.code(brief_text, language=None)
            st.success("Brief displayed above - copy manually")


def render_brief_history(
    briefs: List[Dict[str, Any]],
    max_display: int = 10
) -> None:
    """
    Display history of past operational briefs.
    
    Args:
        briefs: List of brief dictionaries with metadata
        max_display: Maximum number of briefs to display
    """
    logger.debug(f"Rendering brief history with {len(briefs)} briefs")
    
    if not briefs:
        st.info("No brief history available.")
        return
    
    st.markdown("## 📚 Brief History")
    
    # Sort by timestamp (most recent first)
    sorted_briefs = sorted(
        briefs,
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )
    
    # Limit display
    display_briefs = sorted_briefs[:max_display]
    
    if len(briefs) > max_display:
        st.info(f"Showing {max_display} most recent briefs of {len(briefs)} total")
    
    # Display each brief in an expander
    for i, brief_data in enumerate(display_briefs, 1):
        timestamp = brief_data.get('timestamp', 'Unknown')
        brief_text = brief_data.get('brief', 'No content')
        anomaly_count = brief_data.get('num_anomalies', 'N/A')
        severity = brief_data.get('severity', 'Unknown')
        
        # Create expander title
        title = f"Brief #{i} - {timestamp} | {anomaly_count} anomalies | Severity: {severity}"
        
        with st.expander(title, expanded=(i == 1)):
            st.markdown(brief_text)
            
            # Metadata
            if 'metadata' in brief_data:
                st.markdown("---")
                st.markdown("**Metadata:**")
                for key, value in brief_data['metadata'].items():
                    st.write(f"- {key}: {value}")


def render_brief_comparison(
    briefs: List[str],
    labels: Optional[List[str]] = None
) -> None:
    """
    Display multiple briefs side-by-side for comparison.
    
    Args:
        briefs: List of brief texts
        labels: Optional labels for each brief
    """
    logger.debug(f"Rendering brief comparison with {len(briefs)} briefs")
    
    if not briefs:
        st.warning("No briefs to compare.")
        return
    
    if len(briefs) > 3:
        st.warning("Showing first 3 briefs only for comparison.")
        briefs = briefs[:3]
        if labels:
            labels = labels[:3]
    
    st.markdown("## 🔄 Brief Comparison")
    
    # Create columns
    cols = st.columns(len(briefs))
    
    for i, (col, brief) in enumerate(zip(cols, briefs)):
        with col:
            label = labels[i] if labels and i < len(labels) else f"Brief {i+1}"
            st.markdown(f"### {label}")
            st.markdown(brief)


def export_brief(
    brief: str,
    format: str = "markdown",
    filename: Optional[str] = None
) -> None:
    """
    Export operational brief to file.
    
    Args:
        brief: Brief text to export
        format: Export format ('markdown', 'txt', 'html')
        filename: Optional custom filename
    """
    logger.debug(f"Exporting brief in {format} format")
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ops_brief_{timestamp}"
    
    # Prepare content based on format
    if format == 'markdown':
        content = brief
        mime_type = "text/markdown"
        file_ext = ".md"
    elif format == 'txt':
        # Strip markdown formatting for plain text
        content = _strip_markdown(brief)
        mime_type = "text/plain"
        file_ext = ".txt"
    elif format == 'html':
        # Convert markdown to HTML (basic)
        content = _markdown_to_html(brief)
        mime_type = "text/html"
        file_ext = ".html"
    else:
        st.error(f"Unsupported format: {format}")
        return
    
    # Create download button
    st.download_button(
        label=f"Download as {format.upper()}",
        data=content,
        file_name=f"{filename}{file_ext}",
        mime=mime_type
    )


def render_brief_summary(briefs: List[Dict[str, Any]]) -> None:
    """
    Display summary statistics of operational briefs.
    
    Args:
        briefs: List of brief dictionaries
    """
    logger.debug("Rendering brief summary")
    
    if not briefs:
        st.info("No briefs to summarize.")
        return
    
    st.markdown("## 📊 Brief Summary")
    
    # Calculate statistics
    total_briefs = len(briefs)
    
    # Count by severity
    severity_counts = {}
    for brief in briefs:
        severity = brief.get('severity', 'Unknown')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Total anomalies analyzed
    total_anomalies = sum(brief.get('num_anomalies', 0) for brief in briefs)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Briefs", total_briefs)
    
    with col2:
        st.metric("Anomalies Analyzed", total_anomalies)
    
    with col3:
        critical_count = severity_counts.get('Critical', 0) + severity_counts.get('CRITICAL', 0)
        st.metric("Critical Briefs", critical_count)
    
    with col4:
        if briefs:
            latest = briefs[-1].get('timestamp', 'Unknown')
            st.metric("Latest Brief", latest)
    
    # Severity breakdown
    if severity_counts:
        st.markdown("### Severity Breakdown")
        
        severity_df = pd.DataFrame([
            {'Severity': k, 'Count': v}
            for k, v in severity_counts.items()
        ])
        
        st.bar_chart(severity_df.set_index('Severity'))


def render_brief_with_actions(
    brief_text: str,
    anomalies: Optional[List[Dict[str, Any]]] = None
) -> None:
    """
    Display brief with actionable recommendations highlighted.
    
    Args:
        brief_text: Brief text
        anomalies: Optional list of related anomalies
    """
    logger.debug("Rendering brief with actions")
    
    # Display main brief
    render_brief(brief_text)
    
    # Extract and highlight action items
    st.markdown("---")
    st.markdown("### 🎯 Action Items")
    
    # Simple action extraction (look for numbered lists or bullet points)
    action_keywords = ['recommend', 'action', 'should', 'must', 'investigate', 'review', 'check']
    
    lines = brief_text.split('\n')
    actions = []
    
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in action_keywords):
            if line.strip() and (line.strip().startswith('-') or line.strip().startswith('*') or line.strip()[0].isdigit()):
                actions.append(line.strip())
    
    if actions:
        for action in actions:
            st.markdown(f"- {action}")
    else:
        st.info("No specific action items identified in brief.")
    
    # Link to related anomalies
    if anomalies:
        st.markdown("---")
        st.markdown("### 🔗 Related Anomalies")
        st.write(f"This brief covers {len(anomalies)} anomalies")
        
        if st.button("View Related Anomalies"):
            st.session_state['show_anomalies'] = True


def _strip_markdown(text: str) -> str:
    """Remove markdown formatting from text."""
    import re
    
    # Remove headers
    text = re.sub(r'#{1,6}\s+', '', text)
    
    # Remove bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove links
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    return text


def _markdown_to_html(text: str) -> str:
    """Convert markdown to basic HTML."""
    import re
    
    html = text
    
    # Headers
    html = re.sub(r'### (.+)', r'<h3>\1</h3>', html)
    html = re.sub(r'## (.+)', r'<h2>\1</h2>', html)
    html = re.sub(r'# (.+)', r'<h1>\1</h1>', html)
    
    # Bold
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'__(.+?)__', r'<strong>\1</strong>', html)
    
    # Italic
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)
    html = re.sub(r'_(.+?)_', r'<em>\1</em>', html)
    
    # Line breaks
    html = html.replace('\n\n', '</p><p>')
    html = html.replace('\n', '<br>')
    
    # Wrap in HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Operational Brief</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            p {{ line-height: 1.6; }}
        </style>
    </head>
    <body>
        <p>{html}</p>
    </body>
    </html>
    """
    
    return html


# Import pandas for summary statistics
import pandas as pd