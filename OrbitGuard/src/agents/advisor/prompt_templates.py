"""
LLM prompt templates for operational brief generation.

This module contains prompt templates and builders for IBM Granite LLM.
"""

from typing import Dict, Any, Optional


# Main operational brief generation template
ANOMALY_BRIEF_TEMPLATE = """
You are a spacecraft mission control advisor analyzing telemetry anomalies.

Anomaly Details:
- Timestamp: {timestamp}
- Sensor ID: {sensor_id}
- Anomaly Score: {anomaly_score}
- Measured Value: {value}
- Expected Range: {expected_range}

Context:
{context}

Generate a concise operational brief (3 paragraphs) that includes:
1. What happened (technical description)
2. Potential impact on mission operations
3. Recommended immediate actions

Brief:
"""


# Context enrichment template
CONTEXT_ENRICHMENT_TEMPLATE = """
Analyze this spacecraft telemetry anomaly and provide relevant operational context.

Anomaly Data:
{anomaly_data}

Historical Context:
{historical_data}

Provide context about:
- Similar past anomalies
- Affected spacecraft systems
- Mission phase considerations

Context:
"""


# Severity assessment template
SEVERITY_ASSESSMENT_TEMPLATE = """
Assess the severity of this spacecraft telemetry anomaly.

Anomaly Information:
{anomaly_info}

Rate severity as: CRITICAL, HIGH, MEDIUM, or LOW
Provide justification for the rating.

Assessment:
"""


def build_prompt(anomaly: Dict[str, Any], template: str = ANOMALY_BRIEF_TEMPLATE) -> str:
    """
    Construct final prompt from template and anomaly data.
    
    Args:
        anomaly: Dictionary containing anomaly information
        template: Prompt template string
        
    Returns:
        Formatted prompt ready for LLM
    """
    # TODO: Implement prompt building logic
    pass


def format_anomaly_data(anomaly: Dict[str, Any]) -> str:
    """
    Format anomaly data for inclusion in prompts.
    
    Args:
        anomaly: Anomaly data dictionary
        
    Returns:
        Formatted string representation
    """
    # TODO: Implement data formatting logic
    pass
