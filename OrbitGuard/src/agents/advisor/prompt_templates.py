"""
LLM prompt templates for operational brief generation.

This module contains prompt templates and builders for IBM Granite LLM.
Templates are designed to generate clear, actionable operational briefs
from detected telemetry anomalies.
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# Main operational brief generation template
ANOMALY_BRIEF_TEMPLATE = """You are a spacecraft mission control advisor analyzing telemetry anomalies. Your role is to provide clear, actionable operational briefs for mission operators.

**ANOMALY DETAILS:**
- Timestamp: {timestamp}
- Sensor/Channel: {sensor_id}
- Anomaly Score: {anomaly_score} (confidence: {confidence})
- Measured Value: {value}
- Expected Range: {expected_range}
- Deviation: {deviation}

**CONTEXT:**
{context}

**TASK:**
Generate a concise operational brief (3-4 paragraphs) that includes:

1. **What Happened** - Technical description of the anomaly
2. **Potential Impact** - How this affects mission operations and spacecraft health
3. **Recommended Actions** - Immediate steps for mission control team
4. **Monitoring Plan** - What to watch for in subsequent telemetry passes

Keep the tone professional and technical. Focus on actionable information.

**OPERATIONAL BRIEF:**
"""


# Batch anomalies brief template
BATCH_ANOMALIES_TEMPLATE = """You are a spacecraft mission control advisor analyzing multiple telemetry anomalies detected in the same time window.

**ANOMALY SUMMARY:**
Total Anomalies Detected: {total_anomalies}
Time Window: {time_window}
Affected Systems: {affected_systems}

**DETAILED ANOMALIES:**
{anomalies_list}

**TASK:**
Generate a comprehensive operational brief that:

1. **Executive Summary** - High-level overview of the situation
2. **Priority Ranking** - List anomalies by severity (Critical → High → Medium → Low)
3. **System Analysis** - Identify patterns or correlations between anomalies
4. **Recommended Actions** - Prioritized action plan for mission control
5. **Risk Assessment** - Potential mission impact if issues persist

Focus on the big picture while highlighting critical individual anomalies.

**COMPREHENSIVE OPERATIONAL BRIEF:**
"""


# Context enrichment template
CONTEXT_ENRICHMENT_TEMPLATE = """Analyze this spacecraft telemetry anomaly and provide relevant operational context.

**ANOMALY DATA:**
{anomaly_data}

**HISTORICAL CONTEXT:**
{historical_data}

**SPACECRAFT SYSTEMS:**
{systems_info}

Provide context about:
- Similar past anomalies and their outcomes
- Affected spacecraft subsystems and dependencies
- Current mission phase considerations
- Environmental factors (orbital position, solar activity, etc.)

**CONTEXT:**
"""


# Severity assessment template
SEVERITY_ASSESSMENT_TEMPLATE = """Assess the severity of this spacecraft telemetry anomaly for mission operations.

**ANOMALY INFORMATION:**
{anomaly_info}

**ASSESSMENT CRITERIA:**
- CRITICAL: Immediate threat to spacecraft or mission success
- HIGH: Significant impact requiring urgent attention
- MEDIUM: Notable deviation requiring investigation
- LOW: Minor anomaly, monitor but no immediate action needed

Rate severity as: CRITICAL, HIGH, MEDIUM, or LOW

Provide:
1. Severity rating with confidence level
2. Justification based on technical factors
3. Time sensitivity (immediate, hours, days)

**SEVERITY ASSESSMENT:**
"""


# Root cause analysis template
ROOT_CAUSE_TEMPLATE = """Perform root cause analysis for this spacecraft telemetry anomaly.

**ANOMALY DETAILS:**
{anomaly_details}

**SYSTEM INFORMATION:**
{system_info}

**RECENT EVENTS:**
{recent_events}

Analyze potential root causes:
1. Hardware issues (sensors, components, degradation)
2. Software/command issues (configuration, timing, logic)
3. Environmental factors (radiation, thermal, orbital)
4. Operational factors (recent maneuvers, mode changes)

Provide:
- Most likely root cause(s) with confidence level
- Supporting evidence from the data
- Recommended diagnostic steps

**ROOT CAUSE ANALYSIS:**
"""


# Trend analysis template
TREND_ANALYSIS_TEMPLATE = """Analyze trends in spacecraft telemetry anomalies over time.

**ANOMALY HISTORY:**
{anomaly_history}

**TIME PERIOD:**
{time_period}

Identify:
1. Increasing/decreasing anomaly rates
2. Recurring patterns (time-based, system-based)
3. Correlation with mission events
4. Degradation indicators

Provide trend analysis and predictions for future monitoring.

**TREND ANALYSIS:**
"""


def build_prompt(
    anomaly: Dict[str, Any],
    template: str = ANOMALY_BRIEF_TEMPLATE,
    include_context: bool = True,
    **kwargs
) -> str:
    """
    Construct final prompt from template and anomaly data.
    
    Args:
        anomaly: Dictionary containing anomaly information
        template: Prompt template string to use
        include_context: Whether to include contextual information
        **kwargs: Additional template variables
        
    Returns:
        Formatted prompt ready for LLM
    """
    logger.debug(f"Building prompt for anomaly at {anomaly.get('timestamp', 'unknown')}")
    
    # Extract and format anomaly data
    timestamp = anomaly.get('timestamp', 'N/A')
    sensor_id = anomaly.get('sensor_id', anomaly.get('channel', 'Unknown'))
    anomaly_score = anomaly.get('anomaly_score', 0.0)
    value = anomaly.get('value', 'N/A')
    
    # Calculate confidence level
    confidence = _calculate_confidence(anomaly_score)
    
    # Determine expected range
    expected_range = _get_expected_range(anomaly)
    
    # Calculate deviation
    deviation = _calculate_deviation(anomaly)
    
    # Build context
    if include_context:
        context = _build_context(anomaly, **kwargs)
    else:
        context = "No additional context available."
    
    # Format the template
    try:
        prompt = template.format(
            timestamp=timestamp,
            sensor_id=sensor_id,
            anomaly_score=f"{anomaly_score:.4f}",
            confidence=confidence,
            value=value,
            expected_range=expected_range,
            deviation=deviation,
            context=context,
            **kwargs
        )
        
        logger.debug(f"Prompt built successfully, length: {len(prompt)} characters")
        return prompt
    
    except KeyError as e:
        logger.error(f"Missing template variable: {e}")
        raise ValueError(f"Template requires variable: {e}")


def build_batch_prompt(
    anomalies: List[Dict[str, Any]],
    template: str = BATCH_ANOMALIES_TEMPLATE,
    **kwargs
) -> str:
    """
    Build prompt for multiple anomalies.
    
    Args:
        anomalies: List of anomaly dictionaries
        template: Prompt template to use
        **kwargs: Additional template variables
        
    Returns:
        Formatted prompt for batch analysis
    """
    logger.info(f"Building batch prompt for {len(anomalies)} anomalies")
    
    # Calculate summary statistics
    total_anomalies = len(anomalies)
    
    # Determine time window
    timestamps = [a.get('timestamp') for a in anomalies if 'timestamp' in a]
    if timestamps:
        time_window = f"{min(timestamps)} to {max(timestamps)}"
    else:
        time_window = "Unknown"
    
    # Identify affected systems
    sensors = set(a.get('sensor_id', a.get('channel', 'Unknown')) for a in anomalies)
    affected_systems = ", ".join(sorted(sensors))
    
    # Format individual anomalies
    anomalies_list = _format_anomalies_list(anomalies)
    
    # Format the template
    prompt = template.format(
        total_anomalies=total_anomalies,
        time_window=time_window,
        affected_systems=affected_systems,
        anomalies_list=anomalies_list,
        **kwargs
    )
    
    logger.debug(f"Batch prompt built, length: {len(prompt)} characters")
    return prompt


def format_anomaly_data(anomaly: Dict[str, Any], detailed: bool = True) -> str:
    """
    Format anomaly data for inclusion in prompts.
    
    Args:
        anomaly: Anomaly data dictionary
        detailed: Whether to include detailed information
        
    Returns:
        Formatted string representation
    """
    lines = []
    
    # Basic information
    lines.append(f"Timestamp: {anomaly.get('timestamp', 'N/A')}")
    lines.append(f"Sensor/Channel: {anomaly.get('sensor_id', anomaly.get('channel', 'Unknown'))}")
    lines.append(f"Value: {anomaly.get('value', 'N/A')}")
    lines.append(f"Anomaly Score: {anomaly.get('anomaly_score', 0.0):.4f}")
    
    if detailed:
        # Additional details
        if 'anomaly_rank' in anomaly:
            lines.append(f"Rank: {anomaly['anomaly_rank']}")
        
        if 'predicted_anomaly' in anomaly:
            lines.append(f"Classification: {'Anomaly' if anomaly['predicted_anomaly'] else 'Normal'}")
        
        # Statistical information
        for key in ['mean', 'std', 'min', 'max']:
            if key in anomaly:
                lines.append(f"{key.capitalize()}: {anomaly[key]:.4f}")
    
    return "\n".join(lines)


def _calculate_confidence(anomaly_score: float) -> str:
    """Calculate confidence level from anomaly score."""
    if anomaly_score >= 0.9:
        return "Very High"
    elif anomaly_score >= 0.75:
        return "High"
    elif anomaly_score >= 0.5:
        return "Medium"
    else:
        return "Low"


def _get_expected_range(anomaly: Dict[str, Any]) -> str:
    """Determine expected range for the sensor."""
    if 'expected_min' in anomaly and 'expected_max' in anomaly:
        return f"{anomaly['expected_min']:.2f} to {anomaly['expected_max']:.2f}"
    elif 'mean' in anomaly and 'std' in anomaly:
        mean = anomaly['mean']
        std = anomaly['std']
        return f"{mean - 2*std:.2f} to {mean + 2*std:.2f} (±2σ)"
    else:
        return "Not available"


def _calculate_deviation(anomaly: Dict[str, Any]) -> str:
    """Calculate deviation from expected values."""
    value = anomaly.get('value')
    
    if value is None:
        return "N/A"
    
    if 'mean' in anomaly and 'std' in anomaly:
        mean = anomaly['mean']
        std = anomaly['std']
        
        if std > 0:
            z_score = abs((value - mean) / std)
            return f"{z_score:.2f}σ from mean"
    
    if 'expected_min' in anomaly and 'expected_max' in anomaly:
        exp_min = anomaly['expected_min']
        exp_max = anomaly['expected_max']
        
        if value < exp_min:
            deviation_pct = ((exp_min - value) / exp_min) * 100
            return f"{deviation_pct:.1f}% below minimum"
        elif value > exp_max:
            deviation_pct = ((value - exp_max) / exp_max) * 100
            return f"{deviation_pct:.1f}% above maximum"
    
    return "Within range"


def _build_context(anomaly: Dict[str, Any], **kwargs) -> str:
    """Build contextual information for the anomaly."""
    context_parts = []
    
    # System context
    sensor_id = anomaly.get('sensor_id', anomaly.get('channel', 'Unknown'))
    system_type = _identify_system_type(sensor_id)
    context_parts.append(f"System Type: {system_type}")
    
    # Temporal context
    if 'timestamp' in anomaly:
        context_parts.append(f"Detection Time: {anomaly['timestamp']}")
    
    # Statistical context
    if 'anomaly_rank' in anomaly:
        context_parts.append(f"Severity Rank: {anomaly['anomaly_rank']} (lower is more severe)")
    
    # Additional context from kwargs
    if 'mission_phase' in kwargs:
        context_parts.append(f"Mission Phase: {kwargs['mission_phase']}")
    
    if 'recent_events' in kwargs:
        context_parts.append(f"Recent Events: {kwargs['recent_events']}")
    
    if 'historical_anomalies' in kwargs:
        context_parts.append(f"Historical Context: {kwargs['historical_anomalies']}")
    
    return "\n".join(context_parts)


def _identify_system_type(sensor_id: str) -> str:
    """Identify spacecraft system type from sensor ID."""
    sensor_lower = sensor_id.lower()
    
    if 'temp' in sensor_lower or 'thermal' in sensor_lower:
        return "Thermal Control System"
    elif 'power' in sensor_lower or 'voltage' in sensor_lower or 'current' in sensor_lower:
        return "Power System"
    elif 'pressure' in sensor_lower:
        return "Propulsion/Environmental Control"
    elif 'gyro' in sensor_lower or 'attitude' in sensor_lower:
        return "Attitude Control System"
    elif 'comm' in sensor_lower or 'signal' in sensor_lower:
        return "Communication System"
    else:
        return "General Telemetry"


def _format_anomalies_list(anomalies: List[Dict[str, Any]]) -> str:
    """Format list of anomalies for batch prompt."""
    lines = []
    
    for i, anomaly in enumerate(anomalies, 1):
        lines.append(f"\n**Anomaly #{i}:**")
        lines.append(format_anomaly_data(anomaly, detailed=False))
    
    return "\n".join(lines)


def create_custom_template(
    base_template: str,
    additional_sections: List[str],
    **replacements
) -> str:
    """
    Create a custom prompt template by modifying a base template.
    
    Args:
        base_template: Base template string
        additional_sections: List of additional sections to add
        **replacements: Key-value pairs for template modifications
        
    Returns:
        Modified template string
    """
    template = base_template
    
    # Apply replacements
    for key, value in replacements.items():
        template = template.replace(f"{{{key}}}", str(value))
    
    # Add additional sections
    if additional_sections:
        sections_text = "\n\n".join(additional_sections)
        template = template.replace("**TASK:**", f"{sections_text}\n\n**TASK:**")
    
    logger.debug("Created custom template")
    return template


# Export commonly used templates
TEMPLATES = {
    'brief': ANOMALY_BRIEF_TEMPLATE,
    'batch': BATCH_ANOMALIES_TEMPLATE,
    'context': CONTEXT_ENRICHMENT_TEMPLATE,
    'severity': SEVERITY_ASSESSMENT_TEMPLATE,
    'root_cause': ROOT_CAUSE_TEMPLATE,
    'trend': TREND_ANALYSIS_TEMPLATE
}


def get_template(template_name: str) -> str:
    """
    Get a template by name.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Template string
        
    Raises:
        ValueError: If template name not found
    """
    if template_name not in TEMPLATES:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(TEMPLATES.keys())}")
    
    return TEMPLATES[template_name]